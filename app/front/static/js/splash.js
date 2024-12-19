document.addEventListener("DOMContentLoaded", async () => {
    let memberId = localStorage.getItem("memberId");
    if (memberId == null) {
        try {
            // 멤버 생성 요청
            const res = await fetch(`${BE_SERVER}/members`, {
                method: "POST",
            });
            if (!res.ok) {
                const text = await res.text();
                console.error(`HTTP Error ${res.status}:`, text);
                throw new Error(`HTTP error! status: ${res.status}, message: ${text}`);
            }
            const data = await res.json();
            localStorage.setItem("memberId", data["memberId"]);
            memberId = data["memberId"];

            // 작물 정보 요청
            const cropRes = await fetch(`${BE_SERVER}/crops`);
            if (!cropRes.ok) {
                const text = await cropRes.text();
                console.error(`HTTP Error ${cropRes.status}:`, text);
                throw new Error(`HTTP error! status: ${cropRes.status}, message: ${text}`);
            }
            const cropsData = await cropRes.json();
            const crops_data = {};
            cropsData.forEach(item => {
                crops_data[item.cropName] = {
                    'cropId': item.cropId,
                    'created': false,
                    'threadId': '',
                    'address': ''
                };
            });
            localStorage.setItem("crops_data", JSON.stringify(crops_data));
        } catch (error) {
            alert("멤버 아이디 생성중 오류 발생 : " + error);
            console.error("Fetch error:", error);
            return; // 오류 발생 시 이후 코드를 실행하지 않음
        }
    }

    if (memberId != null) {
        setTimeout(() => {
            const cropsData = JSON.parse(localStorage.getItem("crops_data") || "{}");

            // created가 true인 항목이 하나라도 있는지 확인
            const hasCreatedCrop = Object.values(cropsData).some(crop => crop.created);

            if (!hasCreatedCrop) {
                location.href = `/front/members/${memberId}/recommend`;
            } else {
                location.href = `/front/members/${memberId}`;
            }
        }, 2000);
    } else {
        alert("멤버 아이디가 올바르게 생성되지 않았습니다.");
        window.location.reload();
    }
})
;
