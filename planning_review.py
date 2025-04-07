import requests
import logging
import re
from flask import Flask, request, jsonify


DOORAY_ADMIN_API_URL = "https://admin-api.dooray.com/admin/v1/members"
DOORAY_ADMIN_API_TOKEN = "r4p8dpn3tbv7:SVKeev3aTaerG-q5jyJUgg "  # 토큰



app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_member_id_and_role(mention_text: str):
    """Mentions에서 member ID와 role을 추출하는 함수"""
    pattern = r'dooray://\d+/members/(\d+)\s+"(member|admin)"'
    match = re.search(pattern, mention_text)
    if match:
        return match.group(1), match.group(2)
    return None, None

def get_member_name_by_id(member_id: str) -> str:
    """Dooray Admin API로 구성원 이름을 조회"""
    api_url = f"https://admin-api.dooray.com/admin/v1/members/{member_id}"
    headers = {
        "Authorization": f"dooray-api {DOORAY_ADMIN_API_TOKEN}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get("result", {}).get("name", "알 수 없음")
        else:
            return "알 수 없음"
    except Exception as e:
        logger.exception("❌ 예외 발생 during get_member_name_by_id: %s", e)
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

    # 각 명령어에 대응하는 callbackId 설정
    callback_ids = {
        "/클라일감": "client_task",
        "/기획일감": "planning_task",
        "/품질일감": "qa_task",
        "/캐릭터일감": "character_task",
        "/배경일감": "background_task",
        "/컨셉일감": "concept_task",
        "/애니일감": "animation_task",
        "/이펙트일감": "effect_task",
        "/아트일감": "art_task",
        "/서버일감": "server_task",
        "/TA일감": "ta_task",
        "/테스트일감": "test_task",

    }
    # "/기획리뷰": "planning_review",

    # ✅ Heartbeat 커맨드 추가
    if command == "/heartbeat":
        logger.info("💓 Heartbeat 요청 수신됨")
        return jsonify({"status": "alive"}), 200

    # logger.info("📌 Received command: %s", command)
    # logger.info("📌 Mapped callbackId: %s", callback_ids[command])

    if command in callback_ids:
        dialog_data = {
            "token": cmd_token,
            "triggerId": trigger_id,
            "callbackId": callback_ids[command],  # 변경된 callbackId 사용
            "dialog": {
                "callbackId": callback_ids[command],  # 변경된 callbackId 사용
                "title": "새 업무 등록",
                "submitLabel": "등록",
                "elements": [
                    {"type": "text", "label": "제목", "name": "title", "optional": False},
                    {"type": "textarea", "label": "내용", "name": "content", "optional": False},
                    {"type": "text", "label": "기간", "name": "duration", "optional": False},
                    {"type": "text", "label": "기획서 (URL)", "name": "document", "optional": True},
                    {"type": "text", "label": "담당자 (Dooray ID)", "name": "assignee", "optional": False}
                ]
            }
        }

        headers = {"token": cmd_token, "Content-Type": "application/json"}
        response = requests.post(dooray_dialog_url, json=dialog_data, headers=headers)

        # logger.info("⚠️⚠️⚠️- dialog_data: %s", dialog_data) #
        # 최종적으로 설정된 callbackId 값을 다시 확인하는 로그
        # logger.info("📌 Final dialog_data.callbackId: %s", dialog_data["callbackId"])
        # logger.info("📌 Final dialog_data.dialog.callbackId: %s", dialog_data["dialog"]["callbackId"])

        if response.status_code == 200:
            logger.info(f"✅ Dialog 생성 요청 성공 ({command})")
            return jsonify({"responseType": "ephemeral", "text": "업무 요청이 성공적으로 전송되었습니다!"}), 200
        else:
            logger.error(f"❌ Dialog 생성 요청 실패 ({command}): {response.text}")
            return jsonify({"responseType": "ephemeral", "text": "업무 요청이 전송이 실패했습니다."}), 500


    elif command == "/planning_review":

        logger.info("🛠 /planning_review 진입")

        input_text = data.get("text", "").strip()

        logger.info("🔹 원본 텍스트: %s", input_text)

        # 담당자 필드용 텍스트 준비 (입력 그대로 사용)

        assignee_text = input_text

        dialog_data = {

            "token": cmd_token,

            "triggerId": trigger_id,

            "callbackId": "planning_review_dialog",  # 고유 callbackId 설정

            "dialog": {

                "callbackId": "planning_review_dialog",

                "title": "기획 리뷰 요청",

                "submitLabel": "보내기",

                "elements": [

                    {"type": "text", "label": "담당자", "name": "assignee", "optional": False, "value": assignee_text},

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





    elif command == "/jira2":

        logger.info("jira2 진입")

        input_text = data.get("text", "")

        logger.info("🔹 원본 텍스트: %s", input_text)

        # 멤버 ID 추출
        # 수정된 정규식: 역할 (member/admin) 도 함께 추출
        org_id_pattern = r'\(dooray://3570973280734982045/members/(\d+)\s+"(member|admin)"\)'
        matches = re.findall(org_id_pattern, input_text)
        logger.info("🔹 추출된 멤버 ID 및 역할: %s", matches)

        mention_texts = []
        for member_id, role in matches:
            try:
                api_url = f"https://admin-api.dooray.com/admin/v1/members/{member_id}"
                headers = {
                    "Authorization": "dooray-api r4p8dpn3tbv7:SVKeev3aTaerG-q5jyJUgg"
                }
                resp = requests.get(api_url, headers=headers)
                if resp.status_code == 200:
                    name = resp.json().get("result", {}).get("name", "Unknown")
                    # 역할 반영
                    mention = f"[{name}](dooray://3570973280734982045/members/{member_id} \"{role}\")"
                    mention_texts.append(mention)
                    logger.info("✅ %s (%s, %s) 조회 완료", name, member_id, role)
                else:
                    logger.warning("⚠️ ID %s 조회 실패: %s", member_id, resp.text)
            except Exception as e:
                logger.error("❌ 멤버 조회 예외 발생: %s", e)

        mention_text = " ".join(mention_texts)

        logger.info("🔹 최종 멘션 텍스트: %s", mention_text)

        message_data = {

            "text": f"{mention_text} 📢 Jira 작업을 처리 중입니다...!",

            "channelId": channel_id,

            "triggerId": trigger_id,

            "replaceOriginal": "false",

            "responseType": "inChannel",

            "tenantId": "3570973279848255571"

        }

        headers = {"token": cmd_token, "Content-Type": "application/json"}

        logger.info("🔹 Sending Message Data: %s", message_data)

        # Dooray 메시지 전송

        response = requests.post(responseUrl, json=message_data, headers=headers)

        # Jira Webhook 전송

        jira_webhook_url = "https://projectg.dooray.com/services/3570973280734982045/4037981561969473608/QljyNHwGREyQJsAFbMFp7Q"

        jira_response = requests.post(jira_webhook_url, json=message_data, headers=headers)

        if jira_response.status_code == 200:

            logger.info("✅ Jira 메시지 전송 성공")

        else:

            logger.error("❌ Jira 메시지 전송 실패: %s", jira_response.text)

        if response.status_code == 200:

            logger.info("✅ Dooray 메시지 전송 성공")

            return jsonify({

                "responseType": "inChannel",

                "replaceOriginal": "false",

                "text": f"{mention_text} ✅ Jira 메시지가 전송되었습니다."

            }), 200

        else:

            logger.error("❌ Dooray 메시지 전송 실패: %s", response.text)

            return jsonify({

                "responseType": "inChannel",

                "replaceOriginal": "false",

                "text": "❌ Jira 메시지 전송에 실패했습니다."

            }), 500

    return jsonify({"text": "Unknown command", "responseType": "ephemeral"}), 400


@app.route("/interactive-webhook", methods=["POST"])
def interactive_webhook():
    """Dooray Interactive Message 요청을 처리하는 웹훅"""

    logger.info("⚠️interactive_webhook(): 1 ⚠️")
    data = request.json
    logger.info("📥 Received Interactive Action: %s", data)

    # 필수 데이터 추출
    tenant_domain = data.get("tenantDomain")
    channel_id = data.get("channelId")
    callback_id = data.get("callbackId")
    trigger_id = data.get("triggerId", "")
    submission = data.get("submission", {})
    cmd_token = data.get("cmdToken", "")
    responseUrl = data.get("responseUrl", "")
    commandRequestUrl = data.get("commandRequestUrl", "")

    logger.info("🔹 Final callback_id: %s", callback_id)

    # 채널 ID 확인 및 보정
    if not channel_id:
        channel = data.get("channel")
        if channel:
            channel_id = channel.get("id")
            logger.info("📌 Found channel_id in 'channel' object: %s", channel_id)
        else:
            logger.warning("⚠️ channel_id is missing in both 'channelId' and 'channel' object!")

    logger.info("🔹 Final channel_id: %s", channel_id)

    # 테넌트 도메인 확인 및 보정
    if not tenant_domain:
        tenant = data.get("tenant")
        if tenant:
            tenant_domain = tenant.get("domain")
            logger.info("📌 Found tenant_domain in 'tenant' object: %s", tenant_domain)
        else:
            logger.warning("⚠️ tenant_domain is missing in both 'tenantDomain' and 'tenant' object!")

    logger.info("🔹 Parsed Values:")
    logger.info("   - tenant_domain: %s", tenant_domain)
    logger.info("   - channel_id: %s", channel_id)
    logger.info("   - commandRequestUrl: %s", commandRequestUrl)
    logger.info("   - cmd_token: %s", cmd_token)
    logger.info("   - trigger_id: %s", trigger_id)
    logger.info("   - responseUrl: %s", responseUrl)

    # callback_id와 Dooray Webhook URL 매핑
    jira_webhook_urls = {
        "client_task": "https://projectg.dooray.com/services/3570973280734982045/4038470401618441955/cpWtEVnySIi3mgsxkQT6pA",
        "planning_task": "https://projectg.dooray.com/services/3570973280734982045/4038470695754931917/jX5SWNi7Q5iXgEqMgNT9cw",
        "qa_task": "https://projectg.dooray.com/services/3570973280734982045/4038470969246771241/NHigIPVnSPuHAJpZoR9leg",
        "character_task": "https://projectg.dooray.com/services/3570973280734982045/4038471209127296285/w_ASw7jCSVKOSHdtoGr5ew",
        "background_task": "https://projectg.dooray.com/services/3570973280734982045/4038471696860408308/ITjgr3H5SRipPTObiGKzVA",
        "concept_task": "https://projectg.dooray.com/services/3570973280734982045/4038471868662054018/s65TjLKoQh6_0ZlpMg67NQ",
        "animation_task": "https://projectg.dooray.com/services/3570973280734982045/4038472061012612260/XfHUIwd0Tl6WNYxfJ2ObMw",
        "effect_task": "https://projectg.dooray.com/services/3570973280734982045/4038472364848021171/qMxeiFzTQtKKVcZlEa-Zsg",
        "art_task": "https://projectg.dooray.com/services/3570973280734982045/4038472628237942380/7_dU3COwRUaIOPF02WokmA",
        "server_task": "https://projectg.dooray.com/services/3570973280734982045/4038473828248998749/ZfjTPl4yTLC6Z-qf7dqfYg",
        "ta_task": "https://projectg.dooray.com/services/3570973280734982045/4038474691102299050/GtqG3T4ZQPqmE12IOhypPQ",
        "test_task": "https://projectg.dooray.com/services/3570973280734982045/4037981561969473608/QljyNHwGREyQJsAFbMFp7Q"
    }

    # callbackId가 존재할 경우 해당 URL 할당
    if callback_id in jira_webhook_urls:
        jira_webhook_url = jira_webhook_urls[callback_id]
    else:
        logger.warning("⚠️ Unrecognized callback_id: %s", callback_id)
        return jsonify({"responseType": "ephemeral", "text": "⚠️ 처리할 수 없는 요청입니다."}), 400

    logger.info("⚠️⚠️⚠️- jira_webhook_url: %s", jira_webhook_url)

    # 업무 등록 처리
    if callback_id in jira_webhook_urls:
        if not submission:
            logger.info("⚠️interactive_webhook(): 2 ⚠️")
            return jsonify({"responseType": "ephemeral", "text": "⚠️ 입력된 데이터가 없습니다."}), 400
        logger.info("⚠️inside work_task ⚠️")

        title = submission.get("title", "제목 없음")
        content = submission.get("content", "내용 없음")
        duration = submission.get("duration", "미정")
        document = submission.get("document", "없음")
        assignee = submission.get("assignee", "미정")  # 담당자 추가

        # callback_id에 따른 제목 접두어 설정
        title_prefix = {
            "server_task": "서버-",
            "ta_task": "TA-",
            "client_task": "클라-",
            "planning_task": "기획-",
            "qa_task": "품질-",
            "character_task": "캐릭터-",
            "background_task": "배경-",
            "concept_task": "컨셉-",
            "animation_task": "애니-",
            "effect_task": "이펙트-",
            "art_task": "아트-",
            "test_task": "테스트-",
        }.get(callback_id, "")

        response_data = {
            "responseType": "inChannel",
            "channelId": channel_id,
            "triggerId": trigger_id,
            "replaceOriginal": "false",
            "text": f"[@홍석기C/SGE PM팀](dooray://3570973279848255571/members/3571008351482084031 \"admin\") "  # [@홍석기C/SGE PM팀]
                    f"[@노승한/SGE PM팀](dooray://3570973279848255571/members/3571008626725314977 \"admin\") "  # [@노승한/SGE PM팀]
                    f"[@김주현D/SGE PM팀](dooray://3570973279848255571/members/3898983631689925324 \"member\") \n"  # [@김주현D/SGE PM팀]   
                    f"**지라 일감 요청드립니다.!**\n"
                    f" 제목: {title_prefix}{title}\n"
                    f" 내용: {content}\n"
                    f" 기간: {duration}\n"
                    f" 담당자: {assignee}\n"
                    f" 기획서: {document if document != '없음' else '없음'}"
        }

        # Dooray 메신저로 응답 보내기
        headers = {"Content-Type": "application/json"}
        logger.info("⚠️interactive_webhook(): 3 ⚠️")

        jira_response = requests.post(jira_webhook_url, json=response_data, headers=headers)

        if jira_response.status_code == 200:
            logger.info("⚠️jira_response.status_code == 200: ⚠️")
            return jsonify({"responseType": "inChannel", "text": "✅ 응답이 성공적으로 전송되었습니다!"}), 200
        else:
            logger.error("❌ 메시지 전송 실패: %s", jira_response.text)
            return jsonify({"responseType": "ephemeral", "text": "❌ 응답 전송에 실패했습니다."}), 500

    logger.info("⚠️interactive_webhook(): 5 ⚠️")
    return jsonify({"responseType": "ephemeral", "text": "⚠️ 처리할 수 없는 요청입니다."}), 400


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
    assignee_tags = submission.get("assignee", "")  # 예: (dooray://... "member")

    # mentions 변환
    mentions = []
    for tag in assignee_tags.split():
        member_id, role = extract_member_id_and_role(tag)
        if member_id and role:
            name = get_member_name_by_id(member_id)
            mention = f"[{name}](dooray://3570973280734982045/members/{member_id} \"{role}\")"
            mentions.append(mention)
        else:
            mentions.append(tag)  # 형식이 안 맞을 경우 원본 유지

    assignee_text = " ".join(mentions) if mentions else "없음"

    logger.info("✅ 변환된 assignee mention: %s", assignee_text)
    
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
