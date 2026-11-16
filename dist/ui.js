"use strict";
const $ = (selector) => {
    const element = document.querySelector(selector);
    if (!element)
        throw new Error(`Missing element: ${selector}`);
    return element;
};
let apiKey = localStorage.getItem("groq_api_key") ?? "";
let petName = "";
let species = "";
let tutorialStep = 0;
let voiceEnabled = true;
let parkSpeech = [];
let appleQuestShown = false;
let adventureRunId = 0;
const conversation = $("#conversation");
$("#key").setAttribute("value", apiKey);
function speakJapanese(text) {
    if (!voiceEnabled || !("speechSynthesis" in window) || !text.trim())
        return;
    window.speechSynthesis.cancel();
    const speech = new SpeechSynthesisUtterance(text.replace(/^(NPC|ペット|[^:：]+)[:：]\s*/gm, ""));
    speech.lang = "ja-JP";
    speech.volume = 1;
    speech.rate = 1;
    window.speechSynthesis.speak(speech);
}
function show(id) {
    document.querySelectorAll("section").forEach((section) => {
        const visible = section.id === id;
        section.hidden = !visible;
        section.style.display = visible ? (id === "title" ? "grid" : "block") : "none";
    });
}
function write(text) {
    const bubble = document.createElement("div");
    bubble.className = text.startsWith("あなた:") ? "bubble player" : "bubble pet";
    bubble.textContent = text.replace(/^(あなた|冒険|[^:]+):\s*/, "");
    conversation.appendChild(bubble);
    conversation.scrollTop = conversation.scrollHeight;
}
function showSpeech(text) {
    $("#speech").textContent = text;
}
function hideElement(id) {
    const element = $(id);
    if (element.hidden || element.style.display === "none")
        return;
    element.classList.add("fade-out");
    window.setTimeout(() => {
        element.hidden = true;
        element.style.display = "none";
        element.classList.remove("fade-out");
    }, 450);
}
function showElement(id) {
    const element = $(id);
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
function showTutorial() {
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
function nextTutorial() {
    tutorialStep += 1;
    showTutorial();
}
function setActionLock(locked) {
    const action = (id, enabled) => {
        const button = $(id);
        button.disabled = locked && !enabled;
        button.classList.toggle("tutorial-target", locked && enabled);
    };
    action("#talkButton", tutorialStep === 4);
    action("#adventureButton", false);
    action("#statusButton", tutorialStep === 3);
    const message = $("#msg");
    message.disabled = locked && tutorialStep !== 4;
    message.classList.toggle("tutorial-target", locked && tutorialStep === 4);
    $("#tutorialNext").classList.toggle("tutorial-target", locked && tutorialStep !== 4);
}
function completeTutorialAction() {
    tutorialStep += 1;
    showTutorial();
}
function drawPet(kind) {
    const models = {
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
async function call(action, message = "", extra = {}) {
    const response = await fetch("/api", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, message, key: apiKey, ...extra }),
    });
    const data = await response.json();
    if (!response.ok)
        throw new Error(data.error ?? "通信に失敗しました。");
    return data;
}
function begin() {
    hideElement("#questBoard");
    $("#questBoard").classList.remove("complete");
    hideElement("#spiritOverlay");
    hideElement("#questComplete");
    appleQuestShown = false;
    show("nameSetup");
    apiKey = $("#key").value.trim().replace(/^['"]|['"]$/g, "");
    const localServer = ["localhost", "127.0.0.1"].includes(window.location.hostname);
    if (!apiKey && localServer) {
        apiKey = prompt("Groq APIキーを入力してください。")?.trim() ?? "";
        if (!apiKey) {
            alert("APIキーがないため開始できません。");
            return;
        }
    }
    if ($("#save").checked)
        localStorage.setItem("groq_api_key", apiKey);
    show("nameSetup");
}
function nextName() {
    petName = $("#name").value.trim();
    if (!petName)
        return alert("ペットの名前を入力してください。");
    show("playerSetup");
}
function nextPlayer() {
    if (!$("#player").value.trim())
        return alert("あなたの名前を入力してください。");
    show("speciesSetup");
}
async function start() {
    species = $("#species").value.trim();
    if (!species)
        return alert("種族を入力してください。");
    try {
        const player = $("#player").value.trim();
        await call("start", species, { name: petName, player });
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
    }
    catch (error) {
        alert(error instanceof Error ? error.message : "開始できませんでした。");
    }
}
async function talk() {
    const input = $("#msg");
    const message = input.value.trim();
    if (!message)
        return;
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
    }
    catch (error) {
        alert(`通信エラー: ${error instanceof Error ? error.message : "不明なエラー"}`);
    }
}
async function adventure() {
    show("adventureSelect");
}
async function startPark() {
    const runId = ++adventureRunId;
    try {
        await call("adventure_start");
        $("#parkLog").replaceChildren();
        $("#parkExitButton").disabled = true;
        parkSpeech = [];
        show("parkStage");
        $("#parkLoading").hidden = false;
        $("#parkLoading").style.display = "grid";
        $("#parkLog").hidden = true;
        let done = false;
        do {
            done = await nextPark();
            if (runId !== adventureRunId)
                return;
            if (!done)
                await new Promise((resolve) => window.setTimeout(resolve, 1400));
            if (runId !== adventureRunId)
                return;
        } while (!done);
        $("#parkLoading").hidden = true;
        $("#parkLoading").style.display = "none";
        $("#parkLog").hidden = false;
        $("#parkExitButton").disabled = false;
        $("#parkExitButton").removeAttribute("disabled");
        speakJapanese(parkSpeech.join("\n"));
    }
    catch (error) {
        $("#parkLoading").hidden = true;
        $("#parkLoading").style.display = "none";
        alert(`通信エラー: ${error instanceof Error ? error.message : "不明なエラー"}`);
    }
}
async function nextPark() {
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
            }
            else {
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
function exitPark() {
    adventureRunId += 1;
    if (!$("#parkExitButton").disabled) {
        if ("speechSynthesis" in window)
            window.speechSynthesis.cancel();
        $("#parkLoading").hidden = true;
        $("#parkLoading").style.display = "none";
    }
    show("game");
}
function forceConversationScreen() {
    adventureRunId += 1;
    if ("speechSynthesis" in window)
        window.speechSynthesis.cancel();
    show("game");
}
function toggleVoice() {
    voiceEnabled = !voiceEnabled;
    if (!voiceEnabled && "speechSynthesis" in window)
        window.speechSynthesis.cancel();
    $("#voiceButton").textContent = `読み上げ: ${voiceEnabled ? "ON" : "OFF"}`;
}
async function showStatus() {
    try {
        const result = await call("status");
        write(`知能レベル（IQ）: ${result.iq ?? 3}`);
        write(`プレイヤーへの印象・心の声:\n${result.profile ?? "まだよく分からない。"}`);
        if (tutorialStep === 3)
            completeTutorialAction();
    }
    catch (error) {
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
$("#parkButton").addEventListener("click", startPark);
$("#adventureBackButton").addEventListener("click", exitPark);
$("#parkExitButton").addEventListener("click", exitPark);
$("#voiceButton").addEventListener("click", toggleVoice);
$("#msg").addEventListener("keydown", (event) => {
    if (event.key === "Enter")
        void talk();
});
document.addEventListener("keydown", (event) => {
    if (event.key === "Escape")
        forceConversationScreen();
});
$("#tutorialNext").addEventListener("click", nextTutorial);
Object.assign(window, { begin, nextName, nextPlayer, start, talk, adventure, showStatus });
