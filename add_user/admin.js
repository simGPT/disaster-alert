// API URL
const API_BASE_URL = '/api';
fetch('/api/users')

// 사용자 지역별 조회
async function searchUsers() {
    const region = document.getElementById('region').value;
    const resultDiv = document.getElementById('userResult');
    
    const regionText = region || '전체';
    try {
        // URL 생성
        const url = region 
            ? `${API_BASE_URL}/users?region=${encodeURIComponent(region)}`
            : `${API_BASE_URL}/users`;

        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`오류 발생 : ${response.status}`);
        }
        
        const data = await response.json();

        // 조회 결과 테이블
        if (data.users && data.users.length > 0) {
            let htmlcode = `
                <h3> 조회 결과: ${data.count}명 (${data.region})</h3>
                <table border="1">
                    <thead>
                        <tr style="background-color: #f0f0f0;">
                            <th>ID</th>
                            <th>이름</th>
                            <th>지역</th>
                            <th>이메일</th>
                            <th>등록일</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            data.users.forEach(user => {
                const date = new Date(user.created_at).toLocaleString('ko-KR');
                htmlcode += `
                    <tr>
                        <td>${user.id}</td>
                        <td>${user.name}</td>
                        <td>${user.region}</td>
                        <td>${user.email}</td>
                        <td>${date}</td>
                    </tr>
                `;
            });

            htmlcode += '</tbody></table>';
            resultDiv.innerHTML = htmlcode;
        } else {
            resultDiv.innerHTML = '<p> 해당 지역에 등록되어있는 사용자가 없습니다.</p>';
        }

    } catch (error) {
        console.error('사용자 조회 오류:', error);
        resultDiv.innerHTML = `
            <strong> 오류 발생:</strong> ${error.message}<br>
        `;
    }
}
window.addEventListener('load', () => {
    loadStats();
});
