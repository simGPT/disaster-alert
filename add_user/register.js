// API URL
const API_BASE_URL = '/api';

// 요소 불러오기
const registerForm = document.querySelector('form'); // 또는 특정 ID로 선택
const nameInput = document.querySelector('input[placeholder="이름"]');
const regionSelect = document.querySelector('select');
const emailInput = document.querySelector('input[placeholder="이메일"]');
const submitButton = document.querySelector('button[type="submit"]');

// 사용자 등록하는 메소드
async function registerUser(userData) {
    try {
        const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(userData)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || data.message || '등록에 실패했습니다.');
        }
        return data;
    } catch (error) {
        console.error('등록 오류:', error);
        throw error;
    }
}

if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        // 입력값 확인
        const name = nameInput.value.trim();
        const region = regionSelect.value;
        const email = emailInput.value.trim();

        if (!name || !region || region === '== 거주 지역를 선택하세요 ==' || !email) {
            alert('모든 칸을 입력해주세요.');
            return;
        }

        // 이메일 형식 확인 
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            alert('올바른 이메일 형식을 입력해주세요.');
            return;
        }

        try {
            const userData = {
                name: name,
                region: region,
                email: email
            };

            const result = await registerUser(userData);

            alert('등록이 완료되었습니다!');
            console.log('등록 성공:', result);

            
            registerForm.reset(); // 폼 초기화
        } catch (error) {
            alert(`등록 실패: ${error.message}`);
        }
    });
}
