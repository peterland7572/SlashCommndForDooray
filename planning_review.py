import requests
import logging
import re
from flask import Flask, request, jsonify

DOORAY_ADMIN_API_URL = "https://admin-api.dooray.com/admin/v1/members"
DOORAY_ADMIN_API_TOKEN = "r4p8dpn3tbv7:SVKeev3aTaerG-q5jyJUgg"  # 토큰

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
'''
def get_all_members():
    logger.info("📥 Dooray 전체 멤버 조회 시작")

    api_url = "https://admin-api.dooray.com/admin/v1/members"
    headers = {
        "Authorization": f"dooray-api {DOORAY_ADMIN_API_TOKEN}",
        "Content-Type": "application/json"
    }

    all_members = []
    offset = 0
    limit = 100  # Dooray API가 허용하는 최대 limit 기준 (필요시 더 낮춰도 됨)

    while True:
        paged_url = f"{api_url}?offset={offset}&limit={limit}"
        response = requests.get(paged_url, headers=headers)

        if response.status_code != 200:
            logger.error("❌ 멤버 조회 실패 (%s): %s", response.status_code, response.text)
            break

        result = response.json().get("result", [])
        logger.info("📦 받은 멤버 수 (offset %d): %d", offset, len(result))

        if not result:
            break

        all_members.extend(result)

        if len(result) < limit:
            break

        offset += limit

    logger.info("👥 전체 멤버 수: %d", len(all_members))
    return all_members
'''


def get_all_members():
    logger.info("📥 Dooray 전체 멤버 조회 시작")

    api_url = "https://admin-api.dooray.com/admin/v1/members"
    headers = {
        "Authorization": f"dooray-api {DOORAY_ADMIN_API_TOKEN}",
        "Content-Type": "application/json"
    }

    all_members = []
    page = 0
    limit = 100

    while True:
        paged_url = f"{api_url}?page={page}&limit={limit}"
        try:
            response = requests.get(paged_url, headers=headers)
            response.raise_for_status()
        except Exception as e:
            logger.error("❌ 멤버 조회 실패 (page %d): %s", page, str(e))
            break

        result = response.json().get("result", [])
        logger.info("📦 받은 멤버 수 (page %d): %d", page, len(result))

        if not result:
            break

        all_members.extend(result)

        for i, member in enumerate(result, start=page * limit + 1):
            name = member.get("name", "이름 없음")
            nickname = member.get("nickname", "닉네임 없음")
            user_code = member.get("userCode", "코드 없음")
            email = member.get("emailAddress", "이메일 없음")
            position = member.get("position", "직책 없음")
            department = member.get("department", "부서 없음")
            joined_at = member.get("joinedAt", "입사일 없음")
            role = member.get("tenantMemberRole", "역할 없음")

            logger.info(f"[{i}] 이름: {name}, 닉네임: {nickname}, 코드: {user_code}, 이메일: {email}, "
                        f"직책: {position}, 부서: {department}, 입사일: {joined_at}, 역할: {role}")

        if len(result) < limit:
            break

        page += 1

    logger.info("👥 전체 멤버 수: %d", len(all_members))
    return all_members


def get_member_id_by_name(name):
    logger.info("🔍 이름으로 멤버 조회 시작: '%s'", name)

    members = get_all_members()
    logger.info("👥 가져온 멤버 수: %d", len(members))

    for i, m in enumerate(members):
        m_name = m.get("name")
        m_id = m.get("id")

        logger.debug("🔎 [%d] 이름: '%s', ID: %s", i, m_name, m_id)

        if m_name == name:
            logger.info("✅ 일치하는 멤버 발견: '%s' (id=%s)", m_name, m_id)
            return m_id

    logger.warning("🚫 이름과 일치하는 멤버를 찾지 못함: '%s'", name)
    return None


def extract_member_id_and_role(mention_text: str):
    """Mentions에서 member ID와 role을 추출하는 함수"""
    logger.info("🔍 extract_member_id_and_role(): 입력 mention = %s", mention_text)

    pattern = r'dooray://\d+/members/(\d+)\s+"(member|admin)"'
    match = re.search(pattern, mention_text)

    if match:
        member_id, role = match.group(1), match.group(2)
        logger.info("✅ 추출 성공 - member_id: %s, role: %s", member_id, role)
        return member_id, role
    else:
        logger.warning("⚠️ 추출 실패 - mention 형식이 일치하지 않음: %s", mention_text)
        return None, None


def get_member_name_by_id(member_id: str) -> str:
    """Dooray Admin API로 구성원 이름을 조회"""
    api_url = f"https://admin-api.dooray.com/admin/v1/members/{member_id}"
    headers = {
        "Authorization": f"dooray-api {DOORAY_ADMIN_API_TOKEN}",
        "Content-Type": "application/json"
    }

    logger.info("🔍 get_member_name_by_id(): 시작 - member_id=%s", member_id)
    logger.info("🌐 요청 URL: %s", api_url)
    logger.info("📡 요청 헤더: %s", headers)

    try:
        response = requests.get(api_url, headers=headers)
        logger.info("📥 응답 상태 코드: %s", response.status_code)
        logger.debug("📄 응답 바디 (raw): %s", response.text)

        if response.status_code == 200:
            data = response.json()
            logger.debug("📦 파싱된 JSON: %s", data)

            result = data.get("result")
            if result:
                name = result.get("name")
                if name:
                    logger.info("✅ 이름 추출 성공: %s", name)
                    return name
                else:
                    logger.warning("⚠️ 이름 필드가 존재하지 않음. result=%s", result)
            else:
                logger.warning("⚠️ 'result' 키가 응답에 없음. data=%s", data)
        else:
            logger.error("❌ Dooray API 요청 실패. status_code=%s, 응답=%s", response.status_code, response.text)

    except Exception as e:
        logger.exception("❌ 예외 발생: %s", e)

    return "알 수 없음"


@app.route("/dooray-webhook", methods=["POST"])
def dooray_webhook():
    """Dooray에서 받은 명령을 처리하는 엔드포인트"""
    data = request.json
    logger.info("📥 Received Data: %s", data)

    tenant_domain = data.get("tenantDomain")
    channel_id = data.get("channelId")
    command = data.get("command", "").strip()
    cmd_token = data.get("cmdToken", "")
    trigger_id = data.get("triggerId", "")
    dooray_dialog_url = f"https://{tenant_domain}/messenger/api/channels/{channel_id}/dialogs"
    responseUrl = data.get("responseUrl", "")

    # "/기획리뷰": "planning_review",

    # ✅ Heartbeat 커맨드 추가
    if command == "/heartbeat":
        logger.info("💓 Heartbeat 요청 수신됨")
        return jsonify({"status": "alive"}), 200

        # logger.info("📌 Received command: %s", command)
        # logger.info("📌 Mapped callbackId: %s", callback_ids[command])

    if command == "/planning_review":
        logger.info("🛠 /planning_review 진입")
    
        input_text = data.get("text", "").strip()
        logger.info("🔹 원본 텍스트: %s", input_text)
    
        # ✅ 멘션 추출 (dooray 멘션 포맷)
        mention_pattern = r'\(dooray://\d+/members/(\d+)\s+"(member|admin)"\)'
        mentions = re.findall(mention_pattern, input_text)
        logger.info("🔍 추출된 멤버 수: %d", len(mentions))
    
        assignee_names_list = []
        assignee_ids_list = []
    
        for member_id, role in mentions:
            name = get_member_name_by_id(member_id)
            if name:
                assignee_names_list.append(f"@{name}")
                assignee_ids_list.append(member_id)
                logger.info("👤 이름 매핑: %s → %s", member_id, name)
            else:
                logger.warning("❌ 해당 member_id에 대한 이름을 찾을 수 없습니다: %s", member_id)
    
        # ✅ 최종 포맷
        spacing = ' ' * 100
        assignee_text = f"{' '.join(assignee_names_list)}{spacing}{','.join(assignee_ids_list)}"
        logger.info("✅ 최종 assignee_text: %s", assignee_text)


        dialog_data = {
            "token": cmd_token,
            "triggerId": trigger_id,
            "callbackId": "planning_review_dialog",
            "dialog": {
                "callbackId": "planning_review_dialog",
                "title": "기획 리뷰 요청",
                "submitLabel": "보내기",
                "elements": [
                    {
                        "type": "text",
                        "label": "담당자",
                        "name": "assignee",
                        "optional": False,
                        "value": assignee_text  # ✅ 변환된 멘션 포맷
                    },
                    {"type": "text", "label": "제목", "name": "title", "optional": False},
                    {"type": "text", "label": "기획서 링크", "name": "document", "optional": False},
                    {"type": "textarea", "label": "내용", "name": "content", "optional": False}
                ]
            }
        }

        headers = {"token": cmd_token, "Content-Type": "application/json"}

        response = requests.post(dooray_dialog_url, json=dialog_data, headers=headers)

        if response.status_code == 200:

            logger.info("✅ 기획 리뷰 Dialog 생성 성공")

            return jsonify({

                "responseType": "ephemeral",

                "text": "기획 리뷰 요청을 위한 창이 열렸습니다!"

            }), 200

        else:

            logger.error("❌ 기획 리뷰 Dialog 생성 실패: %s", response.text)

            return jsonify({

                "responseType": "ephemeral",

                "text": "기획 리뷰 요청에 실패했습니다."

            }), 500

    return jsonify({"text": "Unknown command", "responseType": "ephemeral"}), 400


'''
@app.route("/interactive-webhook2", methods=["POST"])
def interactive_webhook2():
    """Dooray /planning_review 요청을 처리하는 웹훅"""

    logger.info("⚠️interactive_webhook2(): 시작 ⚠️")
    data = request.json
    logger.info("📥 Received Interactive Action (planning_review): %s", data)

    tenant_domain = data.get("tenantDomain")
    channel_id = data.get("channelId")
    callback_id = data.get("callbackId")
    trigger_id = data.get("triggerId", "")
    submission = data.get("submission", {})
    cmd_token = data.get("cmdToken", "")
    response_url = data.get("responseUrl", "")
    command_request_url = data.get("commandRequestUrl", "")

    if not submission:
        return jsonify({"responseType": "ephemeral", "text": "⚠️ 입력된 데이터가 없습니다."}), 400

    # 폼 입력값 처리
    title = submission.get("title", "제목 없음")
    content = submission.get("content", "내용 없음")
    document = submission.get("document", "없음")
    assignee_tags = submission.get("assignee", "")  # 여러 명 가능

    mentions = []

    # ✅ '@이름' 형식 추출 (공백 포함된 이름 전체 추출)
    mention_pattern = r'@([^\n,]+)'  # '@조현웅/SGE 품질검증팀' → '조현웅/SGE 품질검증팀'
    names_raw = re.findall(mention_pattern, assignee_tags)
    logger.info("🔍 추출된 이름 개수: %d", len(names_raw))

    for raw_name in names_raw:
        logger.info("🔹 처리 중인 이름: %s", raw_name)

        member_id = get_member_id_by_name(raw_name)
        logger.info("🆔 이름으로 조회한 member_id=%s", member_id)

        if member_id:
            # Dooray 링크는 실제 멤버 ID로 구성
            mention = f"[@{raw_name}](dooray://3570973279848255571/members/{member_id} \"member\")"
            logger.info("📎 생성된 mention: %s", mention)
            mentions.append(mention)
        else:
            logger.warning("❌ 이름으로 member_id를 찾을 수 없음: %s", raw_name)
            mentions.append(f"@{raw_name} (찾을 수 없음)")

    assignee_text = " ".join(mentions) if mentions else "없음"
    logger.info("✅ 최종 assignee mention: %s", assignee_text)

    # 메시지 구성
    response_data = {
        "responseType": "inChannel",
        "channelId": channel_id,
        "triggerId": trigger_id,
        "replaceOriginal": "false",
        "text": f"**[기획 검토 요청]**\n"
                f"제목: {title}\n"
                f"내용: {content}\n"
                f"기획서: {document if document != '없음' else '없음'}\n"
                f"담당자: {assignee_text}"
    }

    webhook_url = "https://projectg.dooray.com/services/3570973280734982045/4037981561969473608/QljyNHwGREyQJsAFbMFp7Q"
    headers = {"Content-Type": "application/json"}

    response = requests.post(webhook_url, json=response_data, headers=headers)

    if response.status_code == 200:
        logger.info("✅ 기획 검토 메시지 전송 성공")
        return jsonify({"responseType": "inChannel", "text": "✅ 기획 검토 요청이 전송되었습니다!"}), 200
    else:
        logger.error("❌ 기획 검토 메시지 전송 실패: %s", response.text)
        return jsonify({"responseType": "ephemeral", "text": "❌ 기획 검토 요청 전송에 실패했습니다."}), 500


'''


@app.route("/interactive-webhook2", methods=["POST"])
def interactive_webhook2():
    """Dooray /planning_review 요청을 처리하는 웹훅"""

    logger.info("⚠️interactive_webhook2(): 시작 ⚠️")
    data = request.json
    logger.info("📥 Received Interactive Action (planning_review): %s", data)

    tenant_domain = data.get("tenantDomain")
    channel_id = data.get("channelId")
    callback_id = data.get("callbackId")
    trigger_id = data.get("triggerId", "")
    submission = data.get("submission", {})
    cmd_token = data.get("cmdToken", "")
    response_url = data.get("responseUrl", "")
    command_request_url = data.get("commandRequestUrl", "")

    if not submission:
        return jsonify({"responseType": "ephemeral", "text": "⚠️ 입력된 데이터가 없습니다."}), 400

    # 폼 입력값 처리
    title = submission.get("title", "제목 없음")
    content = submission.get("content", "내용 없음")
    document = submission.get("document", "없음")
    assignee_tags = submission.get("assignee", "")  # 여러 명 가능

    mentions = []

    # ✅ 여러 멘션 추출 (괄호 포함한 문자열)
    mention_pattern = r'\(dooray://\d+/members/\d+\s+"(?:member|admin)"\)'
    mentions_raw = re.findall(mention_pattern, assignee_tags)
    logger.info("🔍 추출된 mention 개수: %d", len(mentions_raw))

    for mention_text in mentions_raw:
        logger.info("🔹 처리 중인 mention: %s", mention_text)

        member_id, role = extract_member_id_and_role(mention_text)
        logger.info("🔍 추출된 ID 및 역할: member_id=%s, role=%s", member_id, role)

        if member_id and role:
            name = get_member_name_by_id(member_id)
            logger.info("👤 이름 조회 결과: member_id=%s, name=%s", member_id, name)

            # mention = f"[@{name}](dooray://3570973280734982045/members/{member_id} \"{role}\")"
            mention = f"[@{name}](dooray://3570973279848255571/members/{member_id} \"{role}\")"
            logger.info("📎 생성된 mention: %s", mention)

            mentions.append(mention)
        else:
            logger.info("🔁 mention 형식 아님, 원본 유지: %s", mention_text)
            mentions.append(mention_text)

    assignee_text = " ".join(mentions) if mentions else "없음"
    logger.info("✅ 최종 assignee mention: %s", assignee_text)

    # 메시지 구성
    response_data = {
        "responseType": "inChannel",
        "channelId": channel_id,
        "triggerId": trigger_id,
        "replaceOriginal": "false",
        "text": f"**[기획 검토 요청]**\n"
                f"제목: {title}\n"
                f"내용: {content}\n"
                f"기획서: {document if document != '없음' else '없음'}\n"
                f"담당자: {assignee_text}"
    }

    webhook_url = "https://projectg.dooray.com/services/3570973280734982045/4037981561969473608/QljyNHwGREyQJsAFbMFp7Q"
    headers = {"Content-Type": "application/json"}

    response = requests.post(webhook_url, json=response_data, headers=headers)

    if response.status_code == 200:
        logger.info("✅ 기획 검토 메시지 전송 성공")
        return jsonify({"responseType": "inChannel", "text": "✅ 기획 검토 요청이 전송되었습니다!"}), 200
    else:
        logger.error("❌ 기획 검토 메시지 전송 실패: %s", response.text)
        return jsonify({"responseType": "ephemeral", "text": "❌ 기획 검토 요청 전송에 실패했습니다."}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0")
