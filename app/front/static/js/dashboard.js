document.addEventListener("DOMContentLoaded", () => {
    // 현재 날씨 정보 요청
    let select_crop = localStorage.getItem("select_crop");
    let crop_data = JSON.parse(localStorage.getItem("crops_data"))[select_crop];
    fetch(`${BE_SERVER}/weather/current?address=${crop_data.address}`)
        .then(response => {
            if (response.ok){
                return response.json();
            }
        }).then(data => {
            console.log(data);
    })

    // 병해충 알림 요청
    // 재배 길라잡이 요청
})