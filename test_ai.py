import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from openai import OpenAI


state = {
    "pet_name": "",
    "personality": {"やさしさ": 0, "好奇心": 0, "元気": 0},
    "memories": [],
}


PAGE = """<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AIペット育成ゲーム</title>
  <style>
    body { max-width: 720px; margin: 2rem auto; padding: 0 1rem;
           font-family: sans-serif; background: #fff8f0; color: #49352a; }
    .card { background: white; border-radius: 16px; padding: 1rem;
            margin: 1rem 0; box-shadow: 0 2px 10px #0001; }
    input, button { box-sizing: border-box; padding: .7rem; margin: .25rem 0;
                    border: 1px solid #d8c6b8; border-radius: 8px; }
    input { width: 100%; } button { cursor: pointer; background: #ffe0b2; }
    #log { min-height: 180px; white-space: pre-wrap; }
    .row { display: flex; gap: .5rem; } .row input { flex: 1; }
  </style>
</head>
<body>
  <h1>AIペット育成ゲーム</h1>
  <div class="card">
    <input id="key" type="password" placeholder="Groq APIキー（保存されません）">
    <input id="name" placeholder="ペットの名前">
    <button onclick="start()">ゲームを始める</button>
  </div>
  <div class="card">
    <div id="status">まずゲームを始めてください。</div>
    <div id="log"></div>
    <div class="row">
      <input id="message" placeholder="ペットに話しかける" onkeydown="if(event.key==='Enter') talk()">
      <button onclick="talk()">話す</button>
      <button onclick="adventure()">冒険</button>
    </div>
    <button onclick="showStatus()">学習・性格を見る</button>
  </div>
  <script>
    let apiKey = "";
    const log = document.getElementById("log");
    function write(text) { log.textContent += text + "\\n"; log.scrollTop = log.scrollHeight; }
    async function request(action, message = "") {
      const response = await fetch("/api/action", {
        method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify({action, message, api_key: apiKey})
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "通信に失敗しました");
      return data;
    }
    async function start() {
      apiKey = document.getElementById("key").value;
      const name = document.getElementById("name").value.trim();
      if (!apiKey || !name) return alert("APIキーとペット名を入力してください。");
      try {
        await request("start", name);
        document.getElementById("status").textContent = name + "との生活が始まりました。";
        write(name + "が仲間になりました！");
      } catch (error) {
        alert(error.message);
      }
    }
    async function talk() {
      const input = document.getElementById("message");
      if (!input.value.trim()) return;
      const message = input.value; input.value = "";
      try { const data = await request("talk", message); write("あなた: " + message); write(data.answer); }
      catch (error) { alert(error.message); }
    }
    async function adventure() {
      const message = prompt("出会った相手への話題を入力してください。");
      if (!message) return;
      try { const data = await request("adventure", message); write("冒険: " + message); write(data.answer); }
      catch (error) { alert(error.message); }
    }
    async function showStatus() {
      try { const data = await request("status"); write("性格: " + JSON.stringify(data.personality)); write("学習: " + data.memories.join(" / ")); }
      catch (error) { alert(error.message); }
    }
  </script>
</body>
</html>"""


def answer(api_key, action, message):
    if not state["pet_name"]:
        raise ValueError("先にゲームを始めてください。")
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key)
    if action == "adventure":
        system = f"あなたはご近所さんです。ペット「{state['pet_name']}」と穏やかに会話してください。日本語で2〜4文にしてください。"
    else:
        system = f"あなたはペット「{state['pet_name']}」です。日本語で自然に、2〜4文で返答してください。性格は{state['personality']}、学習内容は{state['memories']}です。"
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "system", "content": system}, {"role": "user", "content": message}],
    )
    return response.choices[0].message.content


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/":
            self.send_error(404)
            return
        body = PAGE.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/api/action":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(length))
        try:
            action, message, api_key = data.get("action"), data.get("message", ""), data.get("api_key", "")
            if action == "start":
                state["pet_name"] = message
                state["personality"] = {"やさしさ": 0, "好奇心": 0, "元気": 0}
                state["memories"] = []
                result = {"answer": "開始しました。"}
            elif action == "status":
                result = {"personality": state["personality"], "memories": state["memories"]}
            else:
                result = {"answer": answer(api_key, action, message)}
                state["memories"].append(message)
                state["personality"]["好奇心"] += 1
            body = json.dumps(result, ensure_ascii=False).encode()
            self.send_response(200)
        except (ValueError, KeyError, json.JSONDecodeError) as error:
            body = json.dumps({"error": str(error)}, ensure_ascii=False).encode()
            self.send_response(400)
        except Exception as error:
            body = json.dumps({"error": f"Groqとの通信に失敗しました: {error}"}, ensure_ascii=False).encode()
            self.send_response(502)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


print("ブラウザで http://localhost:8000 を開いてください。終了は Ctrl+C です。", flush=True)
HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
