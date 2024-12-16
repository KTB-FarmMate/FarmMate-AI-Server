function fetchWithRetry(url, options = {}, retries = 3, delay = 1000) {
    return fetch(url, options)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .catch(error => {
            if (retries > 1) {
                return new Promise(resolve =>
                    setTimeout(() => resolve(fetchWithRetry(url, options, retries - 1, delay)), delay)
                );
            }
            throw error;
        });
}

function load_messages(memberId, cropName) {
    const crops_data = JSON.parse(localStorage.getItem('crops_data'));
    console.log(crops_data);
    const threadId = crops_data[cropName].threadId
    const url = `${BE_SERVER}/members/${memberId}/threads/${threadId}`;

    const chat_head = document.querySelector('.chat_head ');
    chat_head.remove();
    const chat_body = document.querySelector('.macro_container');
    const message_list = document.querySelector('.message_list');
    chat_body.remove();
    message_list.style.display = 'flex';

    fetchWithRetry(url, {}, 3, 1000)
        .then(messages => {
            const messageList = document.querySelector(".message_list");
            messageList.innerHTML = ""; // 기존 메시지 초기화
            console.log(messages);
            let idx = 0; // 메시지 순서를 나타내는 인덱스

            messages["messages"].forEach(msg => {
                // [시스템 메시지]를 포함하는 메시지는 건너뜀
                if (!msg.text.includes("[시스템 메시지]")) {
                    // role이 null인 경우 순서(idx)에 따라 user와 assistant로 분리
                    const role = msg.role
                        ? msg.role.toLowerCase()
                        : (idx % 2 === 0 ? "user" : "assistant");

                    const messageElement = role === "user"
                        ? createUserMessage(msg.text)
                        : createAssistantMessage(msg.text);

                    messageList.appendChild(messageElement);
                    idx++; // 인덱스 증가
                }
            });
        })
        .catch(error => {
            console.error("Failed to load messages after retries:", error);
            alert("메시지를 로드하는 중 문제가 발생했습니다.");
        });
}


// 사용자 메시지 생성
function createUserMessage(content) {
    const wrapper = document.createElement("div");
    wrapper.className = "message_list_warpper flex flex-column";

    wrapper.innerHTML = `
        <div class="user">
            <div class="message">
                <span>${content}</span>
            </div>
            <div class="edit_btn">
                <img src="/front/static/img/edit.png" alt="">
            </div>
        </div>
    `;

    return wrapper;
}

// AI 응답 메시지 생성
function createAssistantMessage(content) {
    const wrapper = document.createElement("div");
    wrapper.className = "message_list_warpper flex flex-column";

    wrapper.innerHTML = `
        <div class="assistant">
            <div class="chat_setting">
                <div class="profile_img">
                    <img src="/front/static/img/logo.png" alt="">
                </div>
                <div class="setting_btns flex">
                    <div class="copy">
                        <img src="/front/static/img/copy.png" alt="">
                    </div>
                    <div class="share">
                        <img src="/front/static/img/share.png" alt="">
                    </div>
                    <div class="bookmark" onclick="handleBookmark(this)">
                        <img src="/front/static/img/bookmark.png" alt="">
                    </div>
                </div>
            </div>
            <div class="message">
                <span>${content}</span>
            </div>
        </div>
    `;

    return wrapper;
}


let index = 0; // 현재 출력할 글자의 인덱스
const interval = Math.random(); // 0.1 ~ 0.2초 랜덤 간격 설정

function typeMessage(messageContext) {
    if (index < messageContext.length) {
        messageContext.innerHTML += messageContext[index];
        index++;
        setTimeout(typeMessage, interval); // 다음 글자 출력
    }
}

function send_message(memberId, cropName) {
    // 전송 버튼 비활성화 상태일 경우 함수 종료
    const crops_data = JSON.parse(localStorage.getItem('crops_data'));
    console.log(crops_data);
    const threadId = crops_data[cropName].threadId
    if (!document.querySelector(".send_btn_area").classList.contains("active")) {
        return;
    }

    const sendInput = document.querySelector(".input_area input");
    const messageList = document.querySelector(".message_list");

    const userMessageContent = sendInput.value.trim();
    if (!userMessageContent) {
        alert("메시지를 입력하세요!");
        return;
    }

    // 사용자 메시지를 동적으로 추가
    const userMessage = createUserMessage(userMessageContent);
    messageList.appendChild(userMessage);

    // 입력 필드 초기화
    sendInput.value = "";

    // 서버에 메시지 전송
    fetch(`${BE_SERVER}/members/${memberId}/threads/${threadId}/messages`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({"message": userMessageContent})
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const assistantMessageContent = data["message"];
            // AI 응답 메시지를 동적으로 추가
            const assistantMessage = createAssistantMessage(assistantMessageContent);
            messageList.appendChild(assistantMessage);

            // 스크롤 하단 이동
            messageList.scrollTop = messageList.scrollHeight;
        })
        .catch(error => {
            console.error("Error sending message:", error);
            alert("메시지 전송 중 문제가 발생했습니다.");
        });
}

function handleBookmark(element) {
    // 현재 클릭된 bookmark 버튼을 기준으로 부모 .message_list_warpper 찾기
    const wrapper = element.closest(".message_list_warpper");
    const cropName = get_cropName();
    const memberId = get_memberId();

    if (!wrapper) {
        console.error("message_list_warpper를 찾을 수 없습니다.");
        return;
    }

    const threadId = JSON.parse(localStorage.getItem("crops_data"))[cropName].threadId;

    // user 질문 가져오기
    const userMessage = wrapper.querySelector(".user .message span");
    const question = userMessage ? userMessage.textContent.trim() : "질문 없음";

    // assistant 답변 가져오기
    const assistantMessage = wrapper.querySelector(".assistant .message");
    const answer = assistantMessage ? assistantMessage.textContent.trim() : "답변 없음";

    // 결과 출력
    console.log("질문:", question);
    console.log("답변:", answer);

    fetch(`${BE_SERVER}/members/${memberId}/threads/${threadId}/bookmarks`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            "question": question,
            "answer": answer,
            "chattedAt": "2024-12-16T20:29:10.997Z"
        })
    }).then(r => {
        if (r.ok) {
            return r.json();
        }
    }).then(data => {
        console.log(data);
    })

    // 원하는 작업 수행 (예: localStorage에 저장)
    // saveToBookmarks(question, answer, crop_name);
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