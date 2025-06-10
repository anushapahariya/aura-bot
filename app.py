from flask import Flask, request, jsonify
import boto3
import os

app = Flask(__name__)

# Configuration (use environment variables or replace with actual values)
BEDROCK_REGION = os.environ.get("AWS_REGION", "us-east-2")
KB_ID = os.environ.get("BEDROCK_KB_ID", "MAKZOATKHX")
MODEL_ARN = os.environ.get("MODEL_ARN",
                           "arn:aws:bedrock:us-east-2::foundation-model/anthropic.claude-3-haiku-20240307-v1:0")

# Create Bedrock Agent Runtime client
bedrock_agent_runtime = boto3.client("bedrock-agent-runtime", region_name=BEDROCK_REGION)


@app.route("/")
def form():
    return '''
   <!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Aura Bot Chat</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }

    #chat-toggle {
      position: fixed;
      bottom: 20px;
      right: 20px;
      display: flex;
      align-items: center;
      background: white;
      padding: 10px 15px;
      border-radius: 30px;
      box-shadow: 0 5px 15px rgba(0,0,0,0.3);
      border: 1px solid #ccc;
      cursor: pointer;
      z-index: 1000;
      transition: transform 0.2s ease;
    }

    #chat-toggle:hover {
      transform: scale(1.05);
    }

    #chat-toggle img {
      width: 50px;
      height: 50px;
      border-radius: 50%;
      object-fit: cover;
      margin-right: 10px;
    }

    #chat-toggle span {
      font-size: 18px;
      font-weight: bold;
      color: #333;
      font-family: Arial, sans-serif;
    }

    #chat-box {
      display: none;
      position: fixed;
      bottom: 100px;
      right: 20px;
      width: 350px;
      height: 450px;
      background: white;
      border-radius: 10px;
      box-shadow: 0 5px 15px rgba(0,0,0,0.3);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      font-family: Arial, sans-serif;
      z-index: 999;
    }

    #chat-header {
      background: #007bff;
      color: white;
      padding: 15px;
      font-size: 18px;
      text-align: center;
    }

    #chat-messages {
      flex: 1;
      padding: 10px;
      overflow-y: auto;
      font-size: 14px;
    }

    #chat-input {
      display: flex;
      border-top: 1px solid #ccc;
    }

    #chat-input input {
      flex: 1;
      padding: 12px;
      border: none;
      outline: none;
      font-size: 14px;
    }

    #chat-input button {
      padding: 12px 16px;
      background: #007bff;
      color: white;
      border: none;
      cursor: pointer;
    }

    #chat-input button:hover {
      background: #0056b3;
    }
  </style>
</head>
<body>

<div id="chat-toggle">
  <img src="/static/robot.png" alt="Chat Icon">
  <span>Aura Bot</span>
</div>

<div id="chat-box">
  <div id="chat-header">Aura Bot</div>
  <div id="chat-messages"></div>
  <div id="chat-input">
    <input type="text" id="msg-input" placeholder="Type your message..." />
    <button id="send-btn">Send</button>
  </div>
</div>

<script>
  const chatToggle = document.getElementById("chat-toggle");
  const chatBox = document.getElementById("chat-box");
  const sendBtn = document.getElementById("send-btn");
  const msgInput = document.getElementById("msg-input");
  const chatMessages = document.getElementById("chat-messages");

  chatToggle.onclick = () => {
    chatBox.style.display = (chatBox.style.display === "none" || chatBox.style.display === "") ? "flex" : "none";
  };

  sendBtn.onclick = async () => {
    const msg = msgInput.value.trim();
    if (msg) {
      appendMessage("You", msg);
      msgInput.value = "";

      try {
        const res = await fetch('/ask', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: msg })
        });
        const data = await res.json();
        appendMessage("Aura Bot", data.answer || data.error || "No response.");
      } catch (err) {
        appendMessage("Aura Bot", "Error: " + err.message);
      }
    }
  };

  function appendMessage(sender, text) {
    const div = document.createElement("div");
    div.textContent = `${sender}: ${text}`;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  msgInput.addEventListener("keydown", function(e) {
    if (e.key === "Enter") sendBtn.click();
  });
</script>


</body>
</html>

    '''


@app.route("/ask", methods=["POST"])
def ask_question():
    data = request.get_json()
    question = data.get("question")

    if not question:
        return jsonify({"error": "Missing question"}), 400

    try:
        response = bedrock_agent_runtime.retrieve_and_generate(
            input={"text": question},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": KB_ID,
                    "modelArn": "arn:aws:bedrock:us-east-2:908924925940:inference-profile/us.anthropic.claude-3-haiku-20240307-v1:0"
                }
            }
        )
        answer = response['output']['text']
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)