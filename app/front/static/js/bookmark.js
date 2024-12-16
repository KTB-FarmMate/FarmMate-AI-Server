function load_bookmark(crop_name) {
    // localStorage에서 bookmarks 데이터를 가져오기
    let bookmarks = JSON.parse(localStorage.getItem("bookmarks") || `{
            "감자: [],
            "고구마": [],
            "당근": [],
            "양파": []
        }`);
    let bookmarkList = bookmarks[crop_name];
    console.log(bookmarkList);

    if (!bookmarkList || bookmarkList.length === 0) {
        console.log(`${crop_name}에 저장된 북마크가 없습니다.`);
        return;
    }

    // 현재 날짜 기준으로 주별 구분
    const now = new Date();
    const currentWeekStart = new Date(now.setDate(now.getDate() - now.getDay())); // 이번 주 시작일
    const container = document.querySelector(".bookmark-container");

    // 주별 데이터 그룹화
    let weekGroups = {
        thisWeek: {
            title: "이번주",
            items: []
        }
    };

    // 데이터를 역순으로 순회
    for (let i = bookmarkList.length - 1; i >= 0; i--) {
        const dateEntry = bookmarkList[i];
        const entryDate = new Date(dateEntry.date); // 날짜 정보
        const weekDiff = Math.floor((currentWeekStart - entryDate) / (7 * 24 * 60 * 60 * 1000)); // 주 차이 계산

        const weekKey = weekDiff === 0 ? "thisWeek" : `${weekDiff}주전`;
        if (!weekGroups[weekKey]) {
            weekGroups[weekKey] = {
                title: weekDiff === 0 ? "이번주" : `${weekDiff}주전`,
                items: []
            };
        }

        // 날짜별 아이템 추가
        weekGroups[weekKey].items.push(...dateEntry.items);
    }

    // 섹션 동적으로 생성
    Object.keys(weekGroups).forEach((key) => {
        const group = weekGroups[key];
        if (group.items.length > 0) {
            const section = createWeekSection(group.title);
            group.items.forEach((entry) => {
                const itemHTML = createBookmarkItem(entry);
                section.querySelector(".bookmark_list").appendChild(itemHTML);
            });
            container.appendChild(section);
        }
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

    const title = entry["질문제목"] || "제목 없음";
    const content = entry["질문내용"] || "내용 없음";

    item.innerHTML = `
        <div class="header flex flex-row justify-between">
            <div class="content danger flex flex-row align-center">
                <p>${title}</p>
            </div>
            <div class="toggle">
                <img src="" alt="">
            </div>
        </div>
        <div class="details hidden">
            <p>${content}</p>
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