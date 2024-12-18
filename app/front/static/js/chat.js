/**
 * 메시지의 역할(role)을 결정
 */
function determineRole(role, idx) {
    return role
        ? role.toLowerCase()
        : (idx % 2 === 0 ? "user" : "assistant");
}

/**
 * 메시지 요소를 생성
 */
function createMessageElement(bookmarklist, role, text) {
    return role === "user"
        ? createUserMessage(text)
        : createAssistantMessage(text);
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
    let bookmark_list
    fetch(`${BE_SERVER}/members/${memberId}/threads/${threadId}/bookmarks`, {
        method: 'GET',
    }).then(res => res.json()).then(data => {
        bookmark_list = data;
    })

    fetchWithRetry(url, {}, 5, 1000)
        .then(messages => {
            const messageList = document.querySelector(".message_list");
            messageList.innerHTML = ""; // 기존 메시지 초기화
            console.log("Loaded messages:", messages);

            if (!messages || !Array.isArray(messages["messages"])) {
                throw new Error("Invalid message data format"); // 데이터 검증
            }

            let idx = 0; // 메시지 순서를 나타내는 인덱스

            messages["messages"].forEach(msg => {
                // 메시지 검증: msg.text와 msg.role의 유효성 확인
                if (msg.text && !msg.text.includes("[시스템 메시지]")) {
                    const role = determineRole(msg.role, idx);
                    const messageElement = createMessageElement(bookmark_list, role, msg.text);

                    messageList.appendChild(messageElement);
                    idx++; // 인덱스 증가
                }
            });
        })
        .catch(error => {
            console.error("Failed to load messages after retries:", error);
            alert("메시지를 로드하는 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.");
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
<!--            <div class="edit_btn">-->
<!--                <img src="/front/static/img/edit.png" alt="">-->
<!--            </div>-->
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
                    <div class="bookmark" onclick="handleBookmark(this)" data-bookmarkid="">
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
    fetchWithRetry(`${BE_SERVER}/members/${memberId}/threads/${threadId}/messages`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({"message": userMessageContent})
    })
        .then(response => {
            // 상태 코드와 Content-Type 확인
            if (response.message === undefined) {
                console.warn(`HTTP error! status: ${response.status}`);
                return Promise.reject({error: true, status: response.status});
            }
            return response; // JSON 데이터 반환
        })
        .then(data => {
            if (data.error) {
                console.log(data);
                console.warn(`Server error with status: ${data.status}`);
                return; // 에러가 반환되면 이후 로직 실행 안 함
            }
            console.log(data);

            // 정상 응답 처리
            const assistantMessageContent = data.message; // JSON에서 메시지 추출
            const assistantMessage = createAssistantMessage(assistantMessageContent);
            messageList.appendChild(assistantMessage);

            messageList.scrollTop = messageList.scrollHeight; // 스크롤 하단 이동
        })
        .catch(error => {
            // 네트워크 오류 또는 처리되지 않은 에러
            console.error("Error sending message:", error);
            alert(`메시지 전송 중 오류가 발생했습니다: ${error.status || "알 수 없음"}`);
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

    const img = element.querySelector("img");
    if (element.dataset.bookmarkid === "") {
        img.src = "/front/static/img/bookmark_chk.png";
    } else {
        if (deleteBookmark(memberId, threadId, element.dataset.bookmarkid)) {
            img.src = "/front/static/img/bookmark.png";
        } else {
            console.log("북마크 삭제 실패");
        }
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

    fetchWithRetry(`${BE_SERVER}/members/${memberId}/threads/${threadId}/bookmarks`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            "question": question,
            "answer": answer,
            "chattedAt": new Date().toISOString() // 현재 시간을 ISO 형식으로 자동 설정
        })
    })
        .then(response => {
            if (response.bookmarkId === undefined) {
                console.error(`HTTP error! status: ${response}`);
                return response.text().then(text => { // 에러 응답이 텍스트일 경우
                    throw new Error(`Error Response: ${text}`);
                });
            }
            return response; // 성공 응답만 JSON 파싱
        })
        .then(data => {
            element.dataset.bookmarkId = data.bookmarkId;
            console.log("Bookmark response data:", data);
            // 성공적으로 처리된 데이터를 사용할 수 있음
        })
        .catch(error => {
            console.error("Fetch error while creating bookmark:", error.message);
            alert(`북마크 저장 실패: ${error.message}`); // 사용자에게 에러 메시지 표시
        });


    // 원하는 작업 수행 (예: localStorage에 저장)
    // saveToBookmarks(question, answer, crop_name);
}

function deleteBookmark(memberId, threadId, bookmarkId) {
    fetch(`${BE_SERVER}/members/${memberId}/threads/${threadId}/bookmarks/${bookmarkId}`, {
        method: "POST",
    }).then(response => {
        if (!response.ok) {
            console.error(`HTTP error! status: ${response.status}`);
            return false
        }
    })
    return true;
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