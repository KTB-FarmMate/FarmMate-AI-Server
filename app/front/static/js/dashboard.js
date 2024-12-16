document.addEventListener("DOMContentLoaded", () => {
    // 현재 날씨 정보 요청

    fetch(`${BE_SERVER}/weather/current?address=${address}`)
        .then(response => {
            if (response.ok){
                return response.json();
            }


        })


    // 병해충 알림 요청
    // 재배 길라잡이 요청
})