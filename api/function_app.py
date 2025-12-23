import azure.functions as func
import logging
import json
import os
import psycopg2

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
