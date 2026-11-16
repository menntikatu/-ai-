type ApiResult = {
  answer?: string;
  apple_learned?: boolean;
  done?: boolean;
  line?: string;
  max_turns?: number;
  turn?: number;
  message?: string;
  error?: string;
  personality?: Record<string, number>;
  memories?: string[];
  iq?: number;
  profile?: string;
};

const $ = <T extends HTMLElement>(selector: string): T => {
  const element = document.querySelector<T>(selector);
  if (!element) throw new Error(`Missing element: ${selector}`);
  return element;
};

let apiKey = localStorage.getItem("groq_api_key") ?? "";
let petName = "";
let species = "";
let tutorialStep = 0;
let voiceEnabled = true;
let parkSpeech: string[] = [];
let appleQuestShown = false;
let adventureRunId = 0;
type TestQuestion = {question: string; answer: string};
let testQuestions: TestQuestion[] = [];
let testAnswers: string[] = [];
let testIndex = 0;
const conversation = $("#conversation");
$("#key").setAttribute("value", apiKey);

function speakJapanese(text: string): void {
  if (!voiceEnabled || !("speechSynthesis" in window) || !text.trim()) return;
  window.speechSynthesis.cancel();
  const speech = new SpeechSynthesisUtterance(text.replace(/^(NPC|ペット|[^:：]+)[:：]\s*/gm, ""));
  speech.lang = "ja-JP";
  speech.volume = 1;
  speech.rate = 1;
  window.speechSynthesis.speak(speech);
}

function show(id: string): void {
  document.querySelectorAll<HTMLElement>("section").forEach((section) => {
    const visible = section.id === id;
    section.hidden = !visible;
    section.style.display = visible ? (id === "title" ? "grid" : "block") : "none";
  });
}

function createTestQuestions(level: string): TestQuestion[] {
  if (level === "初級") {
    return Array.from({length: 20}, (_, index) => {
      const a = index + 2;
      const b = (index * 3) % 9 + 1;
      return {question: `${a} + ${b} =`, answer: String(a + b)};
    });
  }
  if (level === "中級") {
    const arithmetic = Array.from({length: 10}, (_, index) => {
      const a = index + 2;
      const b = index % 5 + 2;
      return index % 2 === 0
        ? {question: `${a} × ${b} =`, answer: String(a * b)}
        : {question: `${a * b} ÷ ${b} =`, answer: String(a)};
    });
    const sentences: TestQuestion[] = [
      {question: "「雨が降っているので、傘を持って出かけた。」雨が降っている理由で持った物は？", answer: "傘"},
      {question: "「犬が庭で元気に走る。」走っている場所は？", answer: "庭"},
      {question: "「朝ごはんを食べてから学校へ行く。」先にすることは？", answer: "朝ごはん"},
      {question: "「姉は本を読み、弟は絵を描いた。」絵を描いたのは誰？", answer: "弟"},
      {question: "「赤い花の隣に青い花がある。」青い花の隣にある花は？", answer: "赤い花"},
      {question: "「電車が遅れたため、歩いて帰った。」帰る方法は？", answer: "歩いて"},
      {question: "「冷蔵庫から牛乳を出した。」出した物は？", answer: "牛乳"},
      {question: "「公園で友だちとボールを投げた。」誰と投げた？", answer: "友だち"},
      {question: "「夜になったので、明かりをつけた。」つけた物は？", answer: "明かり"},
      {question: "「先生が黒板に文字を書いた。」文字を書いた人は？", answer: "先生"},
    ];
    return [...arithmetic, ...sentences];
  }
  if (level === "上級") {
    const questions: TestQuestion[] = [
      {question: "x² + 5x + 6 を因数分解", answer: "(x+2)(x+3)"},
      {question: "x² - 7x + 12 を因数分解", answer: "(x-3)(x-4)"},
      {question: "x² - 9 を因数分解", answer: "(x-3)(x+3)"},
      {question: "x² + 7x + 10 を因数分解", answer: "(x+2)(x+5)"},
      {question: "√49 =", answer: "7"},
      {question: "√81 =", answer: "9"},
      {question: "√144 =", answer: "12"},
      {question: "√25 + √16 =", answer: "9"},
      {question: "「知識」の読み方", answer: "ちしき"},
      {question: "「成長」の読み方", answer: "せいちょう"},
      {question: "「冒険」の読み方", answer: "ぼうけん"},
      {question: "「記憶」の読み方", answer: "きおく"},
      {question: "「好奇心」の読み方", answer: "こうきしん"},
      {question: "「自然」の読み方", answer: "しぜん"},
      {question: "「判断」の読み方", answer: "はんだん"},
      {question: "「理解」の読み方", answer: "りかい"},
      {question: "「性格」の読み方", answer: "せいかく"},
      {question: "「会話」の読み方", answer: "かいわ"},
      {question: "「学習」の読み方", answer: "がくしゅう"},
      {question: "「経験」の読み方", answer: "けいけん"},
    ];
    return questions;
  }
  return [
    {question: "y = x² - 4x + 3 の頂点の x 座標", answer: "2"},
    {question: "y = x² - 4x + 3 の頂点の y 座標", answer: "-1"},
    {question: "x² - 5x + 6 = 0 の解（小さい順に , 区切り）", answer: "2,3"},
    {question: "x² - 7x + 10 = 0 の解（小さい順に , 区切り）", answer: "2,5"},
    {question: "y = x² + 2x - 3 の頂点の x 座標", answer: "-1"},
    {question: "y = x² + 2x - 3 の頂点の y 座標", answer: "-4"},
    {question: "x² - x - 6 = 0 の解（小さい順に , 区切り）", answer: "-2,3"},
    {question: "x² + x - 6 = 0 の解（小さい順に , 区切り）", answer: "-3,2"},
    {question: "y = x² - 6x + 8 の頂点の x 座標", answer: "3"},
    {question: "y = x² - 6x + 8 の頂点の y 座標", answer: "-1"},
  ];
}

function normalizeAnswer(value: string): string {
  return value.trim().toLowerCase().replace(/[（）()\s]/g, "").replace(/、/g, ",");
}

function startTest(): void {
  const level = $<HTMLSelectElement>("#testLevel").value;
  testQuestions = createTestQuestions(level);
  testAnswers = [];
  testIndex = 0;
  $("#testLevelName").textContent = level;
  show("test");
  renderTestQuestion();
}

function renderTestQuestion(): void {
  const question = testQuestions[testIndex];
  $("#testProgress").textContent = `${testIndex + 1} / ${testQuestions.length} 問`;
  $("#testQuestion").textContent = question.question;
  const answer = $<HTMLInputElement>("#testAnswer");
  answer.value = "";
  answer.focus();
  $<HTMLButtonElement>("#testNextButton").textContent = testIndex + 1 === testQuestions.length ? "採点する" : "次の問題";
}

function nextTestQuestion(): void {
  testAnswers[testIndex] = $<HTMLInputElement>("#testAnswer").value;
  if (testIndex + 1 < testQuestions.length) {
    testIndex += 1;
    renderTestQuestion();
    return;
  }
  const mistakes = testQuestions.flatMap((question, index) =>
    normalizeAnswer(testAnswers[index]) === normalizeAnswer(question.answer) ? [] : [{
      index: index + 1, question: question.question, answer: testAnswers[index] || "未回答", correct: question.answer,
    }]);
  $("#testScore").textContent = `${testQuestions.length - mistakes.length} / ${testQuestions.length} 点`;
  const paper = $("#testPaper");
  paper.replaceChildren();
  mistakes.forEach((mistake) => {
    const row = document.createElement("p");
    row.textContent = `第${mistake.index}問：${mistake.question}｜あなたの答え：${mistake.answer}｜正解：${mistake.correct}`;
    paper.appendChild(row);
  });
  if (mistakes.length === 0) {
    paper.textContent = "全問正解です！";
  }
  show("testResult");
}

function write(text: string): void {
  const bubble = document.createElement("div");
  bubble.className = text.startsWith("あなた:") ? "bubble player" : "bubble pet";
  bubble.textContent = text.replace(/^(あなた|冒険|[^:]+):\s*/, "");
  conversation.appendChild(bubble);
  conversation.scrollTop = conversation.scrollHeight;
}

function showSpeech(text: string): void {
  $("#speech").textContent = text;
}

function hideElement(id: string): void {
  const element = $<HTMLElement>(id);
  if (element.hidden || element.style.display === "none") return;
  element.classList.add("fade-out");
  window.setTimeout(() => {
    element.hidden = true;
    element.style.display = "none";
    element.classList.remove("fade-out");
  }, 450);
}

function showElement(id: string): void {
  const element = $<HTMLElement>(id);
  element.classList.remove("fade-out");
  element.hidden = false;
  element.style.display = id === "#questComplete" ? "grid" : "block";
}

const tutorialSteps = [
  {
    title: "はじめまして、旅人さん",
    text: "わたしは精霊のルミ。ここでは、あなたのペット「名前」の成長を見守ります。まずはペットと仲良くなりましょう。",
  },
  {
    title: "ペットを紹介します",
    text: "目の前にいるのが、あなたのペットです。話しかけるたびに、言葉や世界のことを少しずつ学んでいきます。",
  },
  {
    title: "「冒険」で世界へ",
    text: "「冒険」では、通行人やご近所さんと出会えます。ペットが新しい考え方を学ぶ機会です。",
  },
  {
    title: "学習・性格を確認",
    text: "「学習・性格」では、ペットが覚えたことと性格の変化を確認できます。",
  },
  {
    title: "「話す」でペットと会話",
    text: "下の入力欄に言葉を入れて「話す」を押すと、ペットとの会話が吹き出しに表示されます。実際に会話してみましょう！",
  },
];

function showTutorial(): void {
  const step = tutorialSteps[tutorialStep];
  if (!step) {
    hideElement("#tutorial");
    setActionLock(false);
    return;
  }
  $("#tutorialTitle").textContent = step.title;
  $("#tutorialText").textContent = step.text.replace("名前", petName);
  $("#tutorialNext").textContent = "次へ";
  $("#tutorialNext").hidden = tutorialStep >= 4 || tutorialStep === 3;
  setActionLock(true);
  $("#tutorial").classList.remove("fade-out");
  $("#tutorial").style.display = "flex";
  $("#tutorial").hidden = false;
}

function nextTutorial(): void {
  tutorialStep += 1;
  showTutorial();
}

function setActionLock(locked: boolean): void {
  const action = (id: string, enabled: boolean): void => {
    const button = $<HTMLButtonElement>(id);
    button.disabled = locked && !enabled;
    button.classList.toggle("tutorial-target", locked && enabled);
  };
  action("#talkButton", tutorialStep === 4);
  action("#adventureButton", false);
  action("#statusButton", tutorialStep === 3);
  const message = $<HTMLInputElement>("#msg");
  message.disabled = locked && tutorialStep !== 4;
  message.classList.toggle("tutorial-target", locked && tutorialStep === 4);
  $("#tutorialNext").classList.toggle("tutorial-target", locked && tutorialStep !== 4);
}

function completeTutorialAction(): void {
  tutorialStep += 1;
  showTutorial();
}

function drawPet(kind: string): void {
  const models: Record<string, string> = {
    犬: "https://raw.githubusercontent.com/Ariescar/gobkit-free-assets/main/animal/Corgi.glb",
    猫: "https://www.innerscene.com/api/library/standing-cat-cda42538/download",
    人: "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/main/2.0/CesiumMan/glTF-Binary/CesiumMan.glb",
    キツネ: "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/main/2.0/Fox/glTF-Binary/Fox.glb",
    スライム: "https://raw.githubusercontent.com/Ariescar/gobkit-free-assets/main/animal/Jellyfish.glb",
  };
  const viewer = document.createElement("model-viewer");
  viewer.setAttribute("src", models[kind]);
  viewer.setAttribute("alt", `${kind}の3Dペット`);
  viewer.setAttribute("autoplay", "");
  viewer.setAttribute("animation-name", "Survey");
  viewer.setAttribute("camera-controls", "");
  viewer.style.filter = {
    犬: "hue-rotate(25deg) saturate(1.3)",
    猫: "hue-rotate(320deg) saturate(1.2)",
    人: "saturate(.8)",
    キツネ: "hue-rotate(5deg) saturate(1.4)",
    スライム: "hue-rotate(100deg) saturate(1.7) brightness(1.1)",
  }[kind] ?? "";
  viewer.addEventListener("error", () => {
    $("#petAvatar").textContent = "外部3Dモデルを読み込めませんでした。ネット接続を確認してください。";
  });
  $("#petAvatar").replaceChildren(viewer);
}

async function call(action: string, message = "", extra: Record<string, string> = {}): Promise<ApiResult> {
  const response = await fetch("/api", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({action, message, key: apiKey, ...extra}),
  });
  const data = await response.json() as ApiResult;
  if (!response.ok) throw new Error(data.error ?? "通信に失敗しました。");
  return data;
}

function begin(): void {
  hideElement("#questBoard");
  $("#questBoard").classList.remove("complete");
  hideElement("#spiritOverlay");
  hideElement("#questComplete");
  appleQuestShown = false;
  show("nameSetup");
  apiKey = $<HTMLInputElement>("#key").value.trim().replace(/^['"]|['"]$/g, "");
  const localServer = ["localhost", "127.0.0.1"].includes(window.location.hostname);
  if (!apiKey && localServer) {
    apiKey = prompt("Groq APIキーを入力してください。")?.trim() ?? "";
    if (!apiKey) {
      alert("APIキーがないため開始できません。");
      return;
    }
  }
  if ($<HTMLInputElement>("#save").checked) localStorage.setItem("groq_api_key", apiKey);
  show("nameSetup");
}

function nextName(): void {
  petName = $<HTMLInputElement>("#name").value.trim();
  if (!petName) return alert("ペットの名前を入力してください。");
  show("playerSetup");
}

function nextPlayer(): void {
  if (!$<HTMLInputElement>("#player").value.trim()) return alert("あなたの名前を入力してください。");
  show("speciesSetup");
}

async function start(): Promise<void> {
  species = $<HTMLInputElement>("#species").value.trim();
  if (!species) return alert("種族を入力してください。");
  try {
    const player = $<HTMLInputElement>("#player").value.trim();
    await call("start", species, {name: petName, player});
    hideElement("#questBoard");
    $("#questBoard").classList.remove("complete");
    hideElement("#spiritOverlay");
    hideElement("#questComplete");
    conversation.replaceChildren();
    $("#status").textContent = `${player}と${petName}（${species}）の生活`;
    drawPet(species);
    showSpeech(`${petName}がこちらを見ている。`);
    write(`${petName}（${species}）: 仲間になりました！`);
    show("game");
    tutorialStep = 0;
    showTutorial();
  } catch (error) {
    alert(error instanceof Error ? error.message : "開始できませんでした。");
  }
}

async function talk(): Promise<void> {
  const input = $<HTMLInputElement>("#msg");
  const message = input.value.trim();
  if (!message) return;
  input.value = "";
  try {
    const result = await call("talk", message);
    speakJapanese(result.answer ?? "");
    write(`あなた: ${message}`);
    showSpeech(result.answer ?? "");
    write(`${petName}: ${result.answer ?? ""}`);
    if (tutorialStep === 4) {
      tutorialStep = tutorialSteps.length;
      showTutorial();
      showSpeech("おめでとう！返事が返ってきました！");
      const spirit = $("#spiritOverlay");
      spirit.textContent = "精霊: おめでとう！返事が返ってきました！";
      showElement("#spiritOverlay");
      window.setTimeout(() => hideElement("#spiritOverlay"), 3500);
      showElement("#questBoard");
    }
    if (result.apple_learned && !appleQuestShown) {
      appleQuestShown = true;
      $("#questText").textContent = "達成：ペットはりんごを覚えた！";
      $("#questBoard").classList.add("complete");
      showElement("#questComplete");
      const spirit = $("#spiritOverlay");
      spirit.textContent = "精霊: クエスト達成！これからは自由に会話してみよう！";
      showElement("#spiritOverlay");
      window.setTimeout(() => {
        hideElement("#questBoard");
        hideElement("#spiritOverlay");
        hideElement("#questComplete");
      }, 3500);
    }
  } catch (error) {
    alert(`通信エラー: ${error instanceof Error ? error.message : "不明なエラー"}`);
  }
}

async function adventure(): Promise<void> {
  show("adventureSelect");
}

async function startPark(): Promise<void> {
  const runId = ++adventureRunId;
  try {
    await call("adventure_start");
    $<HTMLElement>("#parkLog").replaceChildren();
    $<HTMLButtonElement>("#parkExitButton").disabled = true;
    parkSpeech = [];
    show("parkStage");
    $("#parkLoading").hidden = false;
    $("#parkLoading").style.display = "grid";
    $("#parkLog").hidden = true;
    let done = false;
    do {
      done = await nextPark();
      if (runId !== adventureRunId) return;
      if (!done) await new Promise((resolve) => window.setTimeout(resolve, 1400));
      if (runId !== adventureRunId) return;
    } while (!done);
    $("#parkLoading").hidden = true;
    $("#parkLoading").style.display = "none";
    $("#parkLog").hidden = false;
    $<HTMLButtonElement>("#parkExitButton").disabled = false;
    $<HTMLButtonElement>("#parkExitButton").removeAttribute("disabled");
    speakJapanese(parkSpeech.join("\n"));
  } catch (error) {
    $("#parkLoading").hidden = true;
    $("#parkLoading").style.display = "none";
    alert(`通信エラー: ${error instanceof Error ? error.message : "不明なエラー"}`);
  }
}

async function nextPark(): Promise<boolean> {
  const result = await call("adventure_next");
  if (result.line) {
    parkSpeech.push(result.line);
    result.line.split("\n").map((part) => part.trim()).filter(Boolean).forEach((part) => {
      const line = document.createElement("div");
      const speaker = part.match(/^([^:：]+)[:：]\s*(.*)$/);
      line.className = `park-line ${speaker?.[1] === "ペット" ? "pet-line" : "npc-line"}`;
      if (speaker) {
        const name = document.createElement("strong");
        name.textContent = speaker[1];
        const text = document.createElement("span");
        text.textContent = speaker[2];
        line.append(name, text);
      } else {
        line.textContent = part;
      }
      $("#parkLog").appendChild(line);
    });
    $("#parkLog").scrollTop = $("#parkLog").scrollHeight;
  }
  if (result.done) {
    const end = document.createElement("div");
    end.className = "park-line";
    end.textContent = result.message ?? "会話が終わりました。";
    $("#parkLog").appendChild(end);
  }
  return result.done === true;
}

function exitPark(): void {
  adventureRunId += 1;
  if (!$<HTMLButtonElement>("#parkExitButton").disabled) {
    if ("speechSynthesis" in window) window.speechSynthesis.cancel();
    $<HTMLElement>("#parkLoading").hidden = true;
    $<HTMLElement>("#parkLoading").style.display = "none";
  }
  show("game");
}

function forceConversationScreen(): void {
  adventureRunId += 1;
  if ("speechSynthesis" in window) window.speechSynthesis.cancel();
  show("game");
}

function toggleVoice(): void {
  voiceEnabled = !voiceEnabled;
  if (!voiceEnabled && "speechSynthesis" in window) window.speechSynthesis.cancel();
  $("#voiceButton").textContent = `読み上げ: ${voiceEnabled ? "ON" : "OFF"}`;
}

async function showStatus(): Promise<void> {
  try {
    const result = await call("status");
    write(`知能レベル（IQ）: ${result.iq ?? 3}`);
    write(`プレイヤーへの印象・心の声:\n${result.profile ?? "まだよく分からない。"}`);
    if (tutorialStep === 3) completeTutorialAction();
  } catch (error) {
    alert(error instanceof Error ? error.message : "取得できませんでした。");
  }
}

$("#beginButton").addEventListener("click", begin);
$("#nextNameButton").addEventListener("click", nextName);
$("#nextPlayerButton").addEventListener("click", nextPlayer);
$("#startButton").addEventListener("click", start);
$("#talkButton").addEventListener("click", talk);
$("#adventureButton").addEventListener("click", adventure);
$("#statusButton").addEventListener("click", showStatus);
$<HTMLButtonElement>("#testButton").addEventListener("click", () => show("testSelect"));
$<HTMLButtonElement>("#testStartButton").addEventListener("click", startTest);
$<HTMLButtonElement>("#testNextButton").addEventListener("click", nextTestQuestion);
$<HTMLButtonElement>("#testBackButton").addEventListener("click", () => show("game"));
$<HTMLButtonElement>("#testResultBackButton").addEventListener("click", () => show("game"));
$<HTMLButtonElement>("#parkButton").addEventListener("click", startPark);
$<HTMLButtonElement>("#adventureBackButton").addEventListener("click", exitPark);
$<HTMLButtonElement>("#parkExitButton").addEventListener("click", exitPark);
$<HTMLButtonElement>("#voiceButton").addEventListener("click", toggleVoice);
$<HTMLInputElement>("#msg").addEventListener("keydown", (event) => {
  if (event.key === "Enter") void talk();
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") forceConversationScreen();
});
$<HTMLButtonElement>("#tutorialNext").addEventListener("click", nextTutorial);
Object.assign(window, {begin, nextName, nextPlayer, start, talk, adventure, showStatus});
