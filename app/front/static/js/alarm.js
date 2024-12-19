document.addEventListener("DOMContentLoaded", () => {
    document.querySelector(".alarm").dataset.selected = 'true';
    const toggles = document.querySelectorAll(".toggle");

    toggles.forEach(toggle => {
        toggle.addEventListener("click", () => {
            const alarmItem = toggle.closest(".alarm_item");
            const isOpen = alarmItem.dataset.open === "true";
            // 상태 토글
            alarmItem.dataset.open = isOpen ? "false" : "true";
        });
    });
});