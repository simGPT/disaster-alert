import azure.functions as func
import logging
import json
import os
import psycopg2
import requests

def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        database=os.environ.get("DB_NAME", "postgres"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        port=os.environ.get("DB_PORT", "5432"),
        sslmode="require"
    )

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# 사용자 등록하는 API
@app.route(route="register", methods=["POST"])
def register_user(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('사용자 등록 API 호출')
    
    try:
        # 요청 데이터 파싱
        req_body = req.get_json()
        name = req_body.get('name')
        region = req_body.get('region')
        email = req_body.get('email')
        
        # 유효성 검사
        if not name or not region or not email:
            return func.HttpResponse(
                json.dumps({"error": "이름, 지역, 이메일은 필수입니다"}, ensure_ascii=False),
                status_code=400,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"} # cors때문
            )
        
        # DB 연결
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 중복 이메일 체크
        cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return func.HttpResponse(
                json.dumps({"error": "이미 등록되어있는 이메일입니다"}, ensure_ascii=False),
                status_code=400,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"}
            )
        
        # 사용자 등록
        cursor.execute(
            "INSERT INTO users (name, region, email) VALUES (%s, %s, %s) RETURNING id",
            (name, region, email)
        )
        user_id = cursor.fetchone()[0]
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return func.HttpResponse(
            json.dumps({
                "success": True,
                "message": "등록 완료!",
                "user": {
                    "id": user_id,
                    "name": name,
                    "region": region,
                    "email": email
                }
            }, ensure_ascii=False),
            status_code=201,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"}
        )
        
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "잘못된 JSON 형식입니다"}, ensure_ascii=False),
            status_code=400,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"}
        )
    except Exception as e:
        logging.error(f"에러 발생: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error":f"서버 오류: {str(e)}"}, ensure_ascii=False),
            status_code=500,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"}
        )


# 지역별 사용자 조회 API
@app.route(route="users", methods=["GET"])
def get_users(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('사용자 조회 API 호출')
    
    try:
        # 지역 가져오기
        region = req.params.get('region')
        
        # DB 연결
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if region:
            # 특정 지역의 사용자 조회
            cursor.execute(
                "SELECT id, name, region, email, created_at FROM users WHERE region = %s ORDER BY created_at DESC",
                (region,)
            )
        else:
            # 전체 사용자 조회
            cursor.execute(
                "SELECT id, name, region, email, created_at FROM users ORDER BY created_at DESC"
            )
        
        users = []
        for row in cursor.fetchall():
            users.append({
                "id": row[0],
                "name": row[1],
                "region": row[2],
                "email": row[3],
                "created_at": row[4].isoformat() if row[4] else None
            })
        
        cursor.close()
        conn.close()
        
        return func.HttpResponse(
            json.dumps({
                "success": True,
                "count": len(users),
                "region": region if region else "전체",
                "users": users
            }, ensure_ascii=False),
            status_code=200,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"}
        )
        
    except Exception as e:
        logging.error(f"에러 발생: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"서버 오류: {str(e)}"}, ensure_ascii=False),
            status_code=500,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"}
        )
    
# 재난 발생 후 알림 전송 API
@app.route(route="disaster-alert", methods=["POST"])
def trigger_disaster(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('재난 알림 발송 API 호출됨')
    
    try:
        req_body = req.get_json()
        region = req_body.get('region')
        disaster_type = req_body.get('type', '긴급 상황')
        
        if not region:
            return func.HttpResponse("지역(region)은 필수 입력 사항입니다.", status_code=400)

        # 재난 발생 지역 사용자 이메일만 조회
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # email 리스트
        cursor.execute("SELECT email FROM users WHERE region = %s", (region,))
        rows = cursor.fetchall()
        
        recipients = [{"email": row[0]} for row in rows]
        
        cursor.close()
        conn.close()

        if not recipients:
            return func.HttpResponse(f"{region} 지역에 등록된 사용자가 없습니다.", status_code=404)

        # VMSS 로드 밸런서로 요청 전달
        vmss_url = "http://104.208.80.218:8000/send-emails"
        
        payload = {
            "disaster_info": {
                "region": region,
                "type": disaster_type
            },
            "recipients": recipients
        }

        # VMSS로 전송
        vmss_response = requests.post(vmss_url, json=payload, timeout=120)
        
        return func.HttpResponse(
            json.dumps({
                "success": True,
                "target_region": region,
                "user_count": len(recipients),
                "vmss_status": vmss_response.status_code,
                "message": f"{len(recipients)}명, 재난 알림 요청 완료"
            }, ensure_ascii=False),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"재난 알림 오류: {str(e)}")
        return func.HttpResponse(f"서버 오류: {str(e)}", status_code=500)
