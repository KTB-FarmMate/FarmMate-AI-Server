document.addEventListener("DOMContentLoaded", () => {
    const monthCombo = document.querySelector(".month_combo");
    const leftButton = document.querySelector(".button.left");
    const rightButton = document.querySelector(".button.right");

    // 좌측 버튼 클릭 시 월 감소
    leftButton.addEventListener("click", () => {
        let currentMonth = parseInt(monthCombo.value);
        if (currentMonth > 1) {
            currentMonth--; // 월 감소
        } else {
            currentMonth = 12; // 1월에서 감소하면 12월로 순환
        }
        monthCombo.value = currentMonth;
    });

    // 우측 버튼 클릭 시 월 증가
    rightButton.addEventListener("click", () => {
        let currentMonth = parseInt(monthCombo.value);
        if (currentMonth < 12) {
            currentMonth++; // 월 증가
        } else {
            currentMonth = 1; // 12월에서 증가하면 1월로 순환
        }
        monthCombo.value = currentMonth;
    });
})