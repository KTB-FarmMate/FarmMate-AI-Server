function load_bookmark(memberId, cropName) {
    // localStorage에서 bookmarks 데이터를 가져오기
    const crops_data = JSON.parse(localStorage.getItem("crops_data"));
    const thread_id = crops_data[cropName]?.threadId;
    console.log(crops_data, cropName);
    if (!thread_id) {
        console.error(`${cropName}에 대한 thread_id를 찾을 수 없습니다.`);
        return;
    }

    console.log("thread_id", thread_id);

    const container = document.querySelector(".bookmark-container");
    if (!container) {
        console.error("bookmark-container를 찾을 수 없습니다.");
        return;
    }

    fetch(`${BE_SERVER}/members/${memberId}/threads/${thread_id}/bookmarks`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (!data || data.length === 0) {
                console.log(`${cropName}에 저장된 북마크가 없습니다.`);
                alert("저장된 북마크가 없습니다.");
                return;
            }

            // 현재 날짜 기준으로 주별 구분
            const now = new Date();
            const currentWeekStart = new Date(now.setDate(now.getDate() - now.getDay())); // 이번 주 시작일

            // 주별 데이터 그룹화
            let weekGroups = {
                thisWeek: {
                    title: "이번주",
                    items: []
                }
            };

            // 데이터를 역순으로 순회
            data.forEach(entry => {
                const entryDate = new Date(entry.addedAt); // 추가된 날짜
                const weekDiff = Math.floor((currentWeekStart - entryDate) / (7 * 24 * 60 * 60 * 1000)); // 주 차이 계산

                const weekKey = weekDiff === 0 ? "thisWeek" : `${weekDiff}주전`;
                if (!weekGroups[weekKey]) {
                    weekGroups[weekKey] = {
                        title: weekDiff === 0 ? "이번주" : `${weekDiff}주전`,
                        items: []
                    };
                }

                weekGroups[weekKey].items.push(entry);
            });

            // 기존 컨테이너 초기화
            container.innerHTML = "";

            // 섹션 동적으로 생성
            Object.keys(weekGroups).forEach(key => {
                const group = weekGroups[key];
                if (group.items.length > 0) {
                    const section = createWeekSection(group.title);
                    group.items.forEach(entry => {
                        const itemHTML = createBookmarkItem(entry);
                        section.querySelector(".bookmark_list").appendChild(itemHTML);
                    });
                    container.appendChild(section);
                }
            });
        })
        .catch(error => {
            console.error("Error fetching bookmarks:", error);
        });
}

// 주 섹션 생성 함수
function createWeekSection(title) {
    const section = document.createElement("div");
    section.className = title === "이번주" ? "this_week flex flex-column" : "week_before";

    section.innerHTML = `
        <div class="title">
            <h3>${title}</h3>
        </div>
        <div class="content">
            <div class="bookmark_list flex flex-column"></div>
        </div>
    `;

    return section;
}

// 북마크 아이템 생성 함수
function createBookmarkItem(entry) {
    const item = document.createElement("div");
    item.className = "bookmark_item flex flex-column";
    item.setAttribute("data-open", "false");

    const question = entry.question || "질문 없음";
    const answer = entry.answer || "답변 없음";
    const addedAt = new Date(entry.addedAt).toLocaleString(); // 추가된 시간 포맷팅

    item.innerHTML = `
        <div class="header flex flex-row justify-between">
            <div class="content flex flex-row align-center">
                <p><strong>질문:</strong> ${question}</p>
            </div>
            <div class="toggle">
                <img src="/front/static/img/arrow.png" alt="Toggle">
            </div>
        </div>
        <div class="details hidden">
            <p><strong>답변:</strong> ${answer}</p>
            <p><small>${addedAt}</small></p>
        </div>
    `;

    // 토글 이벤트 추가 (숨김/보임)
    const toggle = item.querySelector(".toggle img");
    const details = item.querySelector(".details");
    toggle.addEventListener("click", () => {
        const bookmarkItem = toggle.closest(".bookmark_item");
        const isOpen = bookmarkItem.dataset.open === "true";
        bookmarkItem.dataset.open = isOpen ? "false" : "true";
        details.classList.toggle("hidden", isOpen);
    });

    return item;
}


document.addEventListener("DOMContentLoaded", () => {
    document.querySelector(".chatbot").dataset.selected = 'true';
    // const toggles = document.querySelectorAll(".toggle");
    // toggles.forEach(toggle => {
    //     toggle.addEventListener("click", () => {
    //         const bookmarkItem = toggle.closest(".bookmark_item");
    //         const isOpen = bookmarkItem.dataset.open === "true";
    //         // 상태 토글
    //         bookmarkItem.dataset.open = isOpen ? "false" : "true";
    //     });
    // });
});