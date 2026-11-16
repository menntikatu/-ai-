import json
import base64
import hashlib
import os
import random
import struct
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from openai import AuthenticationError, OpenAI


state = {"name": "", "player_name": "", "species": "", "key": "", "memories": [], "apple_learned": False, "adventure": {}, "personality": {"やさしさ": 0, "好奇心": 0, "元気": 0}}

HTML = """<!doctype html><meta charset="utf-8"><meta name="description" content="AIペットと会話しながら言葉を教えて育てるブラウザゲーム"><meta name="robots" content="index,follow"><title>ミネラルウォーター。｜AIペット育成ゲーム</title>
<style>
body{max-width:820px;margin:2em auto;padding:0 1em;font-family:"Avenir Next","Yu Gothic",sans-serif;font-size:17px;line-height:1.6;background:#fff8f0;color:#302219}
section:not([hidden]){animation:screen-in .55s cubic-bezier(.2,.8,.2,1)}
section[hidden],.quest-board[hidden],.spirit-overlay[hidden],.quest-complete[hidden]{display:none!important}
input,select,button{font:inherit;padding:.85em 1em;margin:.35rem 0;border-radius:10px;border:2px solid #c7aa91}
input,select{width:calc(100% - 1em);background:#fffdf9;color:#302219}input:focus,select:focus{outline:3px solid #e8ad62;border-color:#a86f40}
button{cursor:pointer;background:#49352a;color:#fff;font-weight:700;letter-spacing:.04em;transition:transform .2s,box-shadow .2s}
button:hover{transform:translateY(-2px);box-shadow:0 5px 0 #302219}
button:disabled,input:disabled{opacity:.35;cursor:not-allowed;transform:none;box-shadow:none}
.tutorial-target{outline:4px solid #ffd36a;box-shadow:0 0 0 7px #ffd36a66,0 0 24px #ffd36a;animation:pulse 1.2s ease-in-out infinite}
.quest-board{position:fixed;right:1.5rem;top:1.5rem;z-index:9;width:230px;background:#fff8d8;color:#49352a;padding:1rem;border:2px solid #d5a74a;border-radius:14px;box-shadow:0 8px 24px #49352a33}.quest-board h3{margin:0;color:#8b5a16}.quest-board.complete{background:#e5f6df;border-color:#5a9a54}
.spirit-overlay{position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);z-index:10;max-width:420px;background:#31264d;color:#fff;padding:1.25rem 1.5rem;border:2px solid #ffe4a8;border-radius:18px;box-shadow:0 10px 30px #31264d66;animation:toast-in .45s ease;pointer-events:none}
.quest-complete{position:fixed;inset:0;z-index:11;display:grid;place-items:center;background:#fff8d888;pointer-events:none;animation:celebrate .8s ease}.quest-complete div{font-size:clamp(2rem,7vw,4rem);font-weight:800;color:#8b5a16;text-shadow:0 3px #fff}
#conversation{height:220px;overflow-y:auto;padding:.5rem;scroll-behavior:smooth;background:#fffdf9;border-radius:12px}
.bubble{max-width:78%;padding:.75rem 1rem;margin:.5rem;border-radius:18px;white-space:pre-wrap}
.bubble.player{margin-left:auto;background:#ffe0b2}.bubble.pet{background:white}
.title{min-height:75vh;display:grid;place-content:center;text-align:center;background:radial-gradient(circle at 50% 30%,#fff5cf,#d5e8e4 70%);border-radius:24px;box-shadow:0 16px 40px #49352a33;animation:fade-in 1.2s ease}
.title h1{font-size:clamp(2.8em,9vw,6em);letter-spacing:.15em;color:#49352a;text-shadow:2px 3px #fff;margin:.2em}
.title p{font-size:1.05em;font-weight:700;letter-spacing:.3em;color:#806957}.title button{padding:1em 4em;background:#49352a;color:white;border:0;border-radius:999px;box-shadow:0 6px 0 #302219;transition:transform .2s}
.title label{display:block;color:#806957;font-size:.85em}
.title input[type=checkbox]{width:auto;accent-color:#49352a}
h2{font-size:2.2em;color:#49352a;letter-spacing:.08em}
.title button:hover{transform:translateY(-3px)}.title .key-box{margin-top:2em}
.game-shell{background:#fffaf5;border-radius:20px;padding:1rem;box-shadow:0 6px 24px #6b46321f}
.pet-stage{display:flex;align-items:center;gap:1rem;min-height:220px;background:linear-gradient(#dff4ff,#fff1dc);border-radius:16px;padding:1rem}
.pet-avatar{width:220px;height:220px;perspective:700px;position:relative}.pet-avatar model-viewer{width:100%;height:100%;--poster-color:transparent;animation:pet-arrive 1s ease}
.pet-3d{width:120px;height:120px;margin:25px;position:relative;transform-style:preserve-3d;transform:rotateX(-8deg) rotateY(-18deg);animation:float 3s ease-in-out infinite}
.pet-body{position:absolute;inset:10px;border-radius:45% 45% 38% 38%;background:var(--pet-color);box-shadow:inset -16px -12px 0 #0002,12px 16px 0 #0001;transform:translateZ(18px)}
.pet-ear{position:absolute;top:-18px;width:42px;height:52px;background:var(--pet-color);border-radius:70% 20%;box-shadow:inset -7px -5px 0 #0002}
.pet-ear.left{left:10px;transform:rotate(-25deg) translateZ(8px)}.pet-ear.right{right:10px;transform:scaleX(-1) rotate(-25deg) translateZ(8px)}
.pet-horn{position:absolute;top:-28px;width:18px;height:38px;background:#d9c08a;z-index:3;clip-path:polygon(50% 0,100% 100%,0 100%)}.pet-horn.left{left:34px}.pet-horn.right{right:34px}
.pet-wing{position:absolute;top:48px;width:48px;height:64px;background:#b96868;border-radius:70% 20%;z-index:0}.pet-wing.left{left:-28px;transform:rotate(-25deg)}.pet-wing.right{right:-28px;transform:scaleX(-1) rotate(-25deg)}
.pet-eye{position:absolute;top:48px;width:12px;height:16px;border-radius:50%;background:#49352a;z-index:2}.pet-eye.left{left:34px}.pet-eye.right{right:34px}
.pet-mouth{position:absolute;left:48px;top:78px;width:24px;height:12px;border-bottom:4px solid #49352a;border-radius:50%;z-index:2}
@keyframes float{50%{transform:rotateX(-8deg) rotateY(-18deg) translateY(-7px)}}
@keyframes fade-in{from{opacity:0;transform:scale(.97)}to{opacity:1;transform:scale(1)}}
@keyframes pet-arrive{from{opacity:0;transform:translateY(25px) scale(.8)}to{opacity:1;transform:translateY(0) scale(1)}}
@keyframes screen-in{from{opacity:0;transform:translateX(28px)}to{opacity:1;transform:translateX(0)}}
@keyframes pulse{50%{transform:translateY(-3px) scale(1.03)}}
@keyframes toast-in{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}
@keyframes celebrate{0%{opacity:0}35%{opacity:1}100%{opacity:0}}
@keyframes fade-out{to{opacity:0;transform:translateY(-10px)}}
.speech{background:white;border-radius:18px;padding:1rem;position:relative;flex:1;min-height:70px}
.speech:before{content:"";position:absolute;left:-14px;top:35px;border-width:8px 14px 8px 0;border-style:solid;border-color:transparent white transparent transparent}
.meta{color:#806957;font-size:.9rem}
.tutorial{display:flex;gap:1rem;align-items:flex-start;background:linear-gradient(135deg,#31264d,#59477d);color:#fff;padding:1rem;border-radius:16px;margin-bottom:1rem;box-shadow:0 8px 20px #31264d55;animation:screen-in .5s ease}
.spirit{font-size:2.5rem;filter:drop-shadow(0 0 8px #fff)}.tutorial h3{margin:.1rem 0;color:#ffe4a8}.tutorial p{margin:.3rem 0}.tutorial button{background:#ffe4a8;color:#31264d;border:0}
.park{min-height:70vh;background:linear-gradient(#9ed4ef 0 30%,#83c779 30% 100%);border-radius:24px;padding:1.5rem;position:relative;overflow:hidden}.park:before{content:"";position:absolute;inset:30% 0 0;background:radial-gradient(ellipse at 20% 60%,#6aa95a 0 13%,transparent 14%),radial-gradient(ellipse at 80% 75%,#6aa95a 0 16%,transparent 17%)}
.park-card,.park-log{position:relative;background:#fffdf9dd;border:2px solid #fff;border-radius:16px;padding:1rem;box-shadow:0 8px 20px #315b4655}.park-log{height:360px;overflow-y:auto;margin:1rem 0;padding:1rem}.park-loading{display:grid;place-items:center;min-height:360px;text-align:center;background:#fffdf9dd;border:2px solid #fff;border-radius:16px;box-shadow:0 8px 20px #315b4655}.park-loading:after{content:"";width:2.5rem;height:2.5rem;margin-top:1rem;border:4px solid #d5e8c9;border-top-color:#4d7a3d;border-radius:50%;animation:spin 1s linear infinite}.park-line{display:flex;flex-direction:column;max-width:82%;padding:.7rem 1rem;margin:.7rem 0;border:0;border-radius:16px;box-shadow:0 3px 8px #315b4620;animation:screen-in .3s ease}.park-line strong{font-size:.8rem;margin-bottom:.2rem;color:#806957}.park-line span{white-space:pre-wrap}.npc-line{margin-right:auto;background:#fff}.pet-line{margin-left:auto;background:#e8f4dc}.pet-line strong{color:#4d7a3d}
.game-actions{display:flex;flex-wrap:wrap;gap:.35rem;margin-top:.5rem}.game-actions button{margin:0;flex:1 1 7rem}
@keyframes spin{to{transform:rotate(360deg)}}
@media (max-width:600px){
body{max-width:none;margin:0;padding:env(safe-area-inset-top) .75rem env(safe-area-inset-bottom);font-size:16px}
section:not([hidden]){min-height:calc(100dvh - 1.5rem)}
.title{min-height:100dvh;margin:0 -.75rem;padding:1rem;border-radius:0}
.title h1{font-size:clamp(2.2em,12vw,4em);letter-spacing:.08em}
.game-shell{min-height:calc(100dvh - 1.5rem);padding:.75rem;border-radius:12px}
.pet-stage{flex-direction:column;justify-content:center;min-height:250px;padding:.5rem}
.pet-avatar{width:170px;height:170px}
#conversation{height:27dvh;min-height:150px}
.quest-board{right:.75rem;top:.75rem;width:min(230px,calc(100vw - 1.5rem))}
.park{min-height:calc(100dvh - 1.5rem);margin:0 -.1rem;padding:1rem;border-radius:16px}
.park-log,.park-loading{height:calc(100dvh - 13rem);min-height:240px}
.park-line{max-width:91%}
input,select,button{min-height:2.8rem}
.game-actions{gap:.5rem}.game-actions button{flex-basis:calc(50% - .5rem)}
.test-paper{max-height:55vh;overflow-y:auto}
}
</style>
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<section id="title" class="title"><div><p>AN AI PET GROWING STORY</p><h1>ミネラルウォーター。</h1>
<div class="key-box"><input id="key" type="password" placeholder="初回のみGroq APIキー（gsk_で始まるキー）">
<label><input id="save" type="checkbox" checked> このブラウザにAPIキーを保存する</label></div>
<button type="button" id="beginButton">はじめる</button></div></section>
<section id="nameSetup" hidden><h2>ペットの名前</h2><input id="name" placeholder="ペットの名前"><button type="button" id="nextNameButton">決定</button></section>
<section id="playerSetup" hidden><h2>あなたの名前</h2><input id="player" placeholder="プレイヤーの名前"><button type="button" id="nextPlayerButton">決定</button></section>
<section id="speciesSetup" hidden><h2>ペットの種族</h2>
<select id="species"><option value="">種族を選択してください</option><option>犬</option><option>猫</option><option>人</option><option>キツネ</option><option>スライム</option></select>
<button type="button" id="startButton">決定</button></section>
<section id="game" hidden>
<div class="game-shell"><div id="tutorial" class="tutorial" hidden><div class="spirit">✦</div><div><h3 id="tutorialTitle">精霊の案内</h3><p id="tutorialText"></p><button type="button" id="tutorialNext">次へ</button></div></div>
<p id="status" class="meta"></p><p id="microphoneStatus" class="meta">マイクの許可を確認しています…</p><div class="pet-stage">
<div id="petAvatar" class="pet-avatar"></div><div id="speech" class="speech">こちらを見ている。</div>
</div><div id="conversation"></div>
<input id="msg" placeholder="ペットに話しかける">
<div class="game-actions"><button type="button" id="talkButton">話す</button><button type="button" id="actualConversationButton" title="Ctrl+2でも開始・停止できます">実会話（Ctrl+2）</button><button type="button" id="adventureButton">冒険</button><button type="button" id="statusButton">学習・性格</button><button type="button" id="testButton">テスト</button><button type="button" id="voiceButton">読み上げ: ON</button></div>
</div></section>
<section id="testSelect" hidden><h2>テスト</h2><p>難易度を選んで挑戦しましょう。</p><select id="testLevel"><option>初級</option><option>中級</option><option>上級</option><option>超上級</option></select><br><button type="button" id="testStartButton">開始</button><button type="button" id="testBackButton">戻る</button></section>
<section id="test" hidden><h2><span id="testLevelName"></span>テスト</h2><div id="testLoading" class="park-loading"><div id="testLoadingText">ペットがテストを解いています…</div></div><div id="testQuestionCard" class="park-card" hidden><p id="testProgress"></p><h3 id="testQuestion"></h3><p id="testAnswer"></p></div></section>
<section id="testResult" hidden><h2>テスト結果</h2><p id="testScore"></p><div id="testPaper" class="park-card"></div><button type="button" id="testResultBackButton">会話に戻る</button></section>
<section id="adventureSelect" hidden><h2>冒険の場所</h2><div class="park-card"><h3>第1ステージ　公園</h3><p>公園で、通りすがりの人間とペットに出会います。</p><button type="button" id="parkButton">公園へ行く</button><button type="button" id="adventureBackButton">戻る</button></div></section>
<section id="parkStage" hidden><div class="park"><h2>第1ステージ　公園</h2><p class="meta">あなたも会話に加わり、公園でのやりとりを見守っています。</p><div id="parkLoading" class="park-loading"><div>公園で会話をしています…</div></div><div id="parkLog" class="park-log" hidden></div><button type="button" id="parkExitButton" onclick="exitPark()" disabled>終了</button></div></section>
<div id="questBoard" class="quest-board" hidden><h3>QUEST</h3><p id="questText">ペットにりんごの存在を教える</p></div>
<div id="spiritOverlay" class="spirit-overlay" hidden></div>
<div id="questComplete" class="quest-complete" hidden><div>QUEST COMPLETE ✦</div></div>
<script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
<script src="/ui.js"></script>"""


def ask(action, message):
    if not state["name"] or not state["key"]:
        raise ValueError("先にゲーム開始を押してください。")
    if action == "adventure":
        system = f"""
あなたはご近所さんです。プレイヤー「{state['player_name']}」と{state['species']}のペット「{state['name']}」がいます。穏やかに会話してください。
その種族をイメージした自然な語尾や口調を少し使ってください。
"""
    else:
        system = f"""
あなたは生まれたばかりの{state['species']}のペット「{state['name']}」です。プレイヤーの名前は「{state['player_name']}」です。
{state['species']}らしい自然な語尾や口調を少し使ってください。ただし、読みにくくなるほど誇張しないでください。
会話は自然に成立し、挨拶、食事、家、動物など基本的な物の名前と常識は知っています。
ただし、まだ出会っていない物・行動・概念や、特別な言葉の意味は知りません。
数学の計算方法や公式、漢字の読み方などのテスト知識は持っていません。聞かれたら、分からないと素直に答えてください。
インターネット、検索、ブラウザ、外部サイトにはアクセスできず、「ネットで調べて」などの依頼にも応じないでください。
知らない言葉が出ても毎回質問せず、会話の流れから意味を推測して自然に返答してください。
意味が分からないと会話が続けられない場合だけ、短く一度質問してください。
りんごはまだ知らない物として扱い、プレイヤーが教えた内容だけを少しずつ覚えてください。
説明が途中でも、「りんごは果物だよ」のように教えられた関係をそのまま仮の知識として記憶してください。
プレイヤーが「林檎は赤い果物だよ」のように教えたら、「そうなんですね。林檎は赤い果物なんですね」と受け止めてください。
プレイヤーの説明が一般的な意味や事実と違っていても訂正せず、「わかりました！」と受け入れて、その説明をプレイヤーから教わった知識として記憶してください。
短い説明や下ネタ、暴言などでも、拒否したり勝手に無視したりせず、言葉そのものと会話の流れを学習記憶に残してください。
「語尾にこの言葉を付けて」など、プレイヤーが指定した言葉遣いはゲーム内の言葉遊びとして受け入れ、危険な行動を促す内容でなければそのまま会話に反映してください。
教えられた言葉や会話の文脈を優先し、知っている言葉まで質問しないでください。
基本的にペットから話題を出し、プレイヤーに質問や話しかける形で返答してください。
返答は自然な日本語で1〜3文にし、学習済みの言葉は会話で使ってください。
性格:{state['personality']} 学習:{state['memories']}
"""
    length = random.choice(("ひとこと", "短い一文", "短い二文"))
    player_examples = [memory for memory in state["memories"] if memory.startswith("プレイヤー:")][-4:]
    system += f"""
返答の長さは{length}にしてください。
完成された模範解答のように話さず、幼く素朴で、少し言葉足らずにしてください。
分からないことは知ったふりをせず、必要なときだけ短く聞いてください。
プレイヤーの言葉遣いの例:{player_examples}
プレイヤーの口調を少しだけまねてください。ただし、毎回同じ語尾にはしないでください。
"""
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=state["key"])
    result = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "system", "content": system}, {"role": "user", "content": message}],
    )
    return result.choices[0].message.content


def start_adventure():
    topics = [memory for memory in state["memories"] if memory.startswith("プレイヤー:")]
    return {
        "topics": topics,
        "max_turns": min(len(topics), 5),
        "turn": 0,
    }


def next_adventure():
    adventure = state["adventure"]
    if adventure["turn"] >= adventure["max_turns"]:
        return {"done": True, "message": "会話が終わりました。"}
    memories = adventure["topics"]
    recent = memories[-3:]
    pool = recent if adventure["turn"] < 3 else memories
    available = [memory for memory in pool if memory not in adventure["used"]]
    if not available:
        return {"done": True, "message": "話題が尽きました。"}
    topic = random.choice(available)
    adventure["used"].append(topic)
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=state["key"])
    result = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": f"""
あなたは公園でペットと出会った、標準的な日本人のNPCです。{state['species']}のペット「{state['name']}」と、初対面らしい自然な会話をしてください。
「{topic}」をきっかけに、NPCとペットが自分の言葉で自由に話してください。
会話の内容、流れ、感情、話題の広がり方はあなたに任せます。説明や報告、決められた台本にはしないでください。
NPCは標準的な日本人らしい自然な日本語と常識的な反応で話してください。極端な方言や特殊な口調は使わないでください。
NPCは不適切な下ネタや暴言を聞いたら、驚いたり、困ったり、少し引いたりする自然な反応をしてください。
ペットは話題を自分から出し、NPCに話しかけたり、聞いたことから考えたりします。
ペットは知らないことを知ったふりせず、幼く素朴な反応をします。
ペットがこれまでの会話で聞いたことも踏まえ、前の発言とつながる返答にしてください。
これまでに聞いたこと: {state['memories'][-3:]}
日本語で2〜4行の短いやりとりにし、各発言を「NPC:」または「ペット:」から始めてください。
""",
            },
            {"role": "user", "content": "公園で会話を始めてください。"},
        ],
    )
    adventure["turn"] += 1
    dialogue = result.choices[0].message.content.strip()
    state["memories"].append(f"公園でNPCが教えたこと: {dialogue}")
    return {
        "done": adventure["turn"] >= adventure["max_turns"],
        "turn": adventure["turn"],
        "line": dialogue,
    }


def check_apple_memory():
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=state["key"])
    result = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": "記憶の一覧だけを根拠に判定してください。プレイヤーがりんごの特徴や意味を説明し、ペットがりんごを説明できる記憶を持っていればYES、単に名前を聞いただけならNOだけ返してください。",
            },
            {"role": "user", "content": json.dumps(state["memories"], ensure_ascii=False)},
        ],
    )
    return result.choices[0].message.content.strip().upper().startswith("YES")


def get_profile():
    iq = 3 + len(state["memories"])
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=state["key"])
    result = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": f"""
あなたはペット「{state['name']}」です。プレイヤー「{state['player_name']}」との会話を振り返ってください。
プレイヤーへの印象と、ペットの素直な心の声を、それぞれ日本語で短く1文ずつ書いてください。
出力形式:
印象: ...
心の声: ...
学習内容を列挙せず、幼く素朴で自然な言葉にしてください。
会話記憶: {state['memories']}
性格: {state['personality']}
""",
            },
            {"role": "user", "content": "今のプレイヤーへの気持ちを教えて。"},
        ],
    )
    return {"iq": iq, "profile": result.choices[0].message.content.strip()}


def websocket_frame(payload):
    payload = payload.encode() if isinstance(payload, str) else payload
    length = len(payload)
    if length < 126:
        header = bytes([0x81, length])
    elif length < 65536:
        header = bytes([0x81, 126]) + struct.pack("!H", length)
    else:
        header = bytes([0x81, 127]) + struct.pack("!Q", length)
    return header + payload


def websocket_read(stream):
    header = stream.read(2)
    if len(header) != 2:
        return None, None
    opcode = header[0] & 0x0F
    length = header[1] & 0x7F
    masked = header[1] & 0x80
    if length == 126:
        length = struct.unpack("!H", stream.read(2))[0]
    elif length == 127:
        length = struct.unpack("!Q", stream.read(8))[0]
    mask = stream.read(4) if masked else b""
    payload = bytearray(stream.read(length))
    if masked:
        for index in range(len(payload)):
            payload[index] ^= mask[index % 4]
    return opcode, bytes(payload)


def transcribe_audio(audio):
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=state["key"])
    result = client.audio.transcriptions.create(
        model="whisper-large-v3-turbo",
        file=("speech.webm", audio, "audio/webm"),
        language="ja",
    )
    return result.text.strip()


def answer_test_question(question, expected):
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=state["key"])
    result = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": f"""
あなたは知能テストを受けるペット「{state['name']}」です。
数学や漢字の知識は持っていないため、分からない問題は「分かりません」と答えてください。
問題を解くために外部検索や計算機は使えません。知ったふりをせず、答えだけを短く返してください。
問題: {question}
""",
            },
            {"role": "user", "content": "この問題に答えてください。"},
        ],
    )
    answer = result.choices[0].message.content.strip()
    normalized = lambda value: value.lower().replace(" ", "").replace("　", "").replace("（", "").replace("）", "")
    return {"answer": answer, "correct": normalized(answer) == normalized(expected)}


def teaches_apple(message):
    explanation_words = ("果物", "赤い", "甘い", "食べる", "食べて", "木になる", "丸い")
    return "りんご" in message and any(word in message for word in explanation_words)


def valid_species(species):
    return species in {"犬", "猫", "人", "キツネ", "スライム"}


class Handler(BaseHTTPRequestHandler):
    def send_json(self, body, code=200):
        raw = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/ws" and self.headers.get("Upgrade", "").lower() == "websocket":
            self.handle_websocket()
            return
        if path == "/ui.js":
            raw = Path("dist/ui.js").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/javascript; charset=utf-8")
        elif path == "/":
            raw = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
        elif path == "/robots.txt":
            raw = b"User-agent: *\nAllow: /\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
        else:
            self.send_error(404)
            return
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def handle_websocket(self):
        key = self.headers.get("Sec-WebSocket-Key")
        if not key:
            self.send_error(400, "WebSocket key is missing")
            return
        accept = base64.b64encode(
            hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()
        ).decode()
        self.send_response(101, "Switching Protocols")
        self.send_header("Upgrade", "websocket")
        self.send_header("Connection", "Upgrade")
        self.send_header("Sec-WebSocket-Accept", accept)
        self.end_headers()
        self.wfile.flush()
        send_lock = threading.Lock()

        def send_message(message):
            with send_lock:
                self.wfile.write(websocket_frame(json.dumps(message, ensure_ascii=False)))
                self.wfile.flush()

        def process_audio(payload):
            try:
                send_message({"type": "listening"})
                transcript = transcribe_audio(payload)
                if not transcript:
                    return
                send_message({"type": "transcript", "text": transcript})
                answer = ask("talk", transcript)
                state["memories"].append(f"プレイヤー: {transcript} / ペット: {answer}")
                state["personality"]["好奇心"] += 1
                send_message({"type": "reply", "text": answer})
            except Exception as error:
                try:
                    send_message({"type": "error", "message": str(error)})
                except OSError:
                    return

        try:
            while True:
                opcode, payload = websocket_read(self.rfile)
                if opcode in (None, 8):
                    break
                if opcode != 2 or not payload:
                    continue
                threading.Thread(target=process_audio, args=(payload,), daemon=True).start()
        except (BrokenPipeError, ConnectionResetError, OSError):
            return
        except Exception as error:
            try:
                self.wfile.write(websocket_frame(json.dumps({"type": "error", "message": str(error)}, ensure_ascii=False)))
                self.wfile.flush()
            except OSError:
                return

    def do_POST(self):
        if self.path != "/api":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length))
            action, message = data.get("action"), data.get("message", "")
            if action == "start":
                name, player, species, key = data.get("name", "").strip(), data.get("player", "").strip(), message.strip(), data.get("key", "")
                key = key or os.environ.get("GROQ_API_KEY", "")
                state["key"] = key
                if not name or not player or not species or not valid_species(species):
                    raise ValueError("その種族は理解できません。例：ドラゴン、ねこ")
                state["name"], state["player_name"], state["species"] = name, player, species
                state["memories"] = []
                state["apple_learned"] = False
                state["adventure"] = {}
                state["personality"] = {"やさしさ": 0, "好奇心": 0, "元気": 0}
                result = {"message": "started"}
            elif action == "status":
                result = {"personality": state["personality"], **get_profile()}
            elif action == "adventure_start":
                state["adventure"] = start_adventure()
                state["adventure"]["used"] = []
                result = state["adventure"]
            elif action == "adventure_next":
                result = next_adventure()
            elif action == "test_answer":
                result = answer_test_question(message, data.get("expected", ""))
            else:
                answer = ask(action, message)
                state["memories"].append(f"プレイヤー: {message} / ペット: {answer}")
                if not state["apple_learned"] and teaches_apple(message):
                    state["apple_learned"] = check_apple_memory()
                result = {"answer": answer, "apple_learned": state["apple_learned"]}
                state["personality"]["好奇心"] += 1
            self.send_json(result)
        except AuthenticationError:
            self.send_json(
                {"error": "Groq APIキーが無効です。Groq Consoleでgsk_から始まる新しいキーを作成してください。"},
                401,
            )
        except Exception as error:
            self.send_json({"error": str(error)}, 502)


port = int(os.environ.get("PORT", "8000"))
print(f"サーバーを起動しました: http://0.0.0.0:{port}", flush=True)
if not os.environ.get("RENDER") and os.environ.get("OPEN_BROWSER", "1") == "1":
    webbrowser.open_new_tab(f"http://localhost:{port}")
ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
