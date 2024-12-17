

function crop_create(crop_name, memberId) {
    const address = document.querySelector("input[name='address']").value;
    const creationDate = document.querySelector("input[name='creation_date']").value;


    const crops_data = JSON.parse(localStorage.getItem("crops_data"));

    let crop_id = crops_data[crop_name].cropId;

    const body = {
        address: address,
        cropId: crop_id,
        plantedAt: creationDate,
    }

    console.log(body);


// 사용 예시
    fetchWithRetry(`${BE_SERVER}/members/${memberId}/threads`, {
        method: "POST",
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
    })
        .then((data) => {
            console.log(data);
            crops_data[crop_name].threadId = data.threadId;
            crops_data[crop_name].created = true;
            crops_data[crop_name].address = address;
            crops_data[crop_name].plantedAt = creationDate;
            localStorage.setItem("crops_data", JSON.stringify(crops_data));

            localStorage.setItem("select_crop", crop_name);
            location.href = `/front/members/${memberId}/crop/${crop_name}`;
        })
        .catch((error) => {
            console.error("Fetch error after retries:", error);
        });
}

function crop_delete(crop_name, memberId) {
    let crops_data = JSON.parse(localStorage.getItem("crops_data"));
    let threadId = crops_data[crop_name].threadId;
    console.log(crops_data, threadId, crop_name)
    // DELETE 요청 사용 예시
    fetchWithRetry(`${BE_SERVER}/members/${memberId}/threads/${threadId}`, {
        method: "DELETE",
        headers: {
            'Content-Type': 'application/json',
        },
    })
        .then(() => {
            crops_data[crop_name].created = false;
            crops_data[crop_name].threadId = '';
            alert("작물 삭제 완료");
            goHome();
        })
        .catch((error) => {
            console.error("Fetch error:", error);
            alert(`작물 삭제 실패: ${error.message}`);
        });
}

function crop_modify(crop_name, memberId) {
    // let memberId = localStorage.getItem("memberId");
    // const memberId = get_memberId;
    // 각 input 요소의 값을 가져옴
    const address = document.querySelector("input[name='address']").value;
    const creationDate = document.querySelector("input[name='creation_date']").value;

    console.log(creationDate)
    const crops_data = JSON.parse(localStorage.getItem("crops_data"));

    // let crop_id = crops_data[crop_name].cropId;

    const body = {
        address: address,
        plantedAt: creationDate,
    }

    console.log(body);

    fetchWithRetry(`${BE_SERVER}/members/${memberId}/threads`, {
        method: "PATCH",
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
    })
        .then((res) => {
            if (!res.ok) {
                console.log(res);
                throw new Error(`HTTP error! status: ${res.status}`);
            }
            return res.json();
        })
        .then(data => {
            console.log(data);
            crops_data[crop_name].threadId = data.threadId;
            crops_data[crop_name].created = true;
            crops_data[crop_name].address = address;
            crops_data[crop_name].plantedAt = creationDate;
            localStorage.setItem("crops_data", JSON.stringify(crops_data));

            localStorage.setItem("select_crop", crop_name);
            location.href = `/MEMBERS/${memberId}/crop/${crop_name}`;
            // localStorage.setItem("memberId", data["memberId"]);
        })
        .catch((error) => {
            console.error("Fetch error:", error);
        });
}