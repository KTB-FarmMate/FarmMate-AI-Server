function send_message(element) {
    if (!element.classList.contains("active")){
        return;
    }
    let send_input = document.querySelector(".input_area input");
    let chat_head = document.querySelector(".chat_head");
    let macro_container = document.querySelector(".macro_container");
    let message_list = document.querySelector(".message_list");
    let user_message = document.querySelector(".user .message span");
    chat_head.style.display = "none";
    macro_container.style.display = "none";
    message_list.style.display = "block";

    let send_message = send_input.value;
    send_input.value = "";

    user_message.textContent = send_message;

    let messageItem = document.querySelector(".assistant .message");
    let messageContext = `
        환경: 서늘하고 반그늘진 곳 선택
        파종:
        - 봄(3-4월) 또는 가을(8-9월)
        - 얕게(0.5cm) 파종, 줄 간격 20cm
        관리:
        - 물: 토양 촉촉하게 유지
        - 간격: 밀집 피하기
        수확:
        - 파종 후 40-50일
        - 필요한 만큼 아래 잎부터 수확
        주의: 더운 여름 피하기, 과습 주의
        
        핵심은 다음과 같습니다:
        1. 상추는 서늘한 환경을 좋아합니다. 너무 더운 여름은 피하세요.
        2. 봄이나 가을에 파종하고, 얕게 심습니다.
        3. 물은 자주 주되, 토양이 너무 습하지 않게 주의
        4. 40-50일 후부터 수확할 수 있으며, 필요한 만큼
        5. 아래 잎부터 따서 사용하면 됩니다.
    `;

    let index = 0; // 현재 출력할 글자의 인덱스
    const interval = Math.random(); // 0.1 ~ 0.2초 랜덤 간격 설정

    function typeMessage() {
        if (index < messageContext.length) {
            messageItem.innerHTML += messageContext[index];
            index++;
            setTimeout(typeMessage, interval); // 다음 글자 출력
        }
    }

    // 메시지 타이핑 시작
    typeMessage();

}
function handleBookmark(element, crop_name) {
    // 현재 클릭된 bookmark 버튼을 기준으로 부모 .message_list_warpper 찾기
    const wrapper = element.closest(".message_list_warpper");

    if (!wrapper) {
        console.error("message_list_warpper를 찾을 수 없습니다.");
        return;
    }

    // user 질문 가져오기
    const userMessage = wrapper.querySelector(".user .message span");
    const question = userMessage ? userMessage.textContent.trim() : "질문 없음";

    // assistant 답변 가져오기
    const assistantMessage = wrapper.querySelector(".assistant .message");
    const answer = assistantMessage ? assistantMessage.textContent.trim() : "답변 없음";

    // 결과 출력
    console.log("질문:", question);
    console.log("답변:", answer);

    // 원하는 작업 수행 (예: localStorage에 저장)
    saveToBookmarks(question, answer, crop_name);
}

function saveToBookmarks(question, answer, crop_name) {
    // localStorage에서 bookmarks 가져오기
    let bookmarks = localStorage.getItem("bookmarks");

    // 초기화 (없으면 기본 구조 생성)
    if (!bookmarks) {
        bookmarks = {
            "감자": [],
            "고구마": [],
            "당근": [],
            "양파": []
        };
    } else {
        bookmarks = JSON.parse(bookmarks);
    }

    // 현재 날짜
    const currentDate = new Date().toISOString().split("T")[0]; // yyyy-mm-dd 형식

    // 작물별 데이터 확인 및 초기화
    if (!bookmarks[crop_name]) {
        bookmarks[crop_name] = [];
    }

    // 해당 날짜에 대한 데이터 찾기
    let todayData = bookmarks[crop_name].find(entry => entry.date === currentDate);

    if (!todayData) {
        // 날짜별 데이터가 없으면 새로 추가
        todayData = {
            date: currentDate,
            items: []
        };
        bookmarks[crop_name].push(todayData);
    }

    // 오늘 날짜 데이터에 새로운 질문/답변 추가
    todayData.items.push({
        "질문제목": question,
        "질문내용": answer
    });

    // localStorage에 저장
    localStorage.setItem("bookmarks", JSON.stringify(bookmarks));

    console.log("북마크가 저장되었습니다:", bookmarks);
}


document.addEventListener("DOMContentLoaded", () => {
    // input 요소와 footer_content, 버튼 영역 가져옴
    const inputArea = document.querySelector(".input_area input");
    const footerContent = document.querySelector(".footer_content");
    const sendButtonArea = document.querySelector(".send_btn_area");

    // input에 focus 시 footer 숨김
    inputArea.addEventListener("focus", () => {
        footerContent.classList.add("hidden");
    });

    // input에 blur 시 footer 보임
    inputArea.addEventListener("blur", () => {
        footerContent.classList.remove("hidden");
    });


    // input 내용에 따라 버튼 상태 업데이트
    inputArea.addEventListener("input", () => {
        if (inputArea.value.trim() !== "") {
            // 값이 있으면 활성화
            sendButtonArea.classList.add("active");
            sendButtonArea.style.pointerEvents = "auto"; // 클릭 가능
        } else {
            // 값이 없으면 비활성화
            sendButtonArea.classList.remove("active");
            sendButtonArea.style.pointerEvents = "none"; // 클릭 불가능
        }
    });



})