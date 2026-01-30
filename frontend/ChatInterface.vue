<template>
  <div class="chat-container">
    <!-- 聊天消息区域 -->
    <div class="messages-container" ref="messagesContainer">
      <div
        v-for="(message, index) in messages"
        :key="index"
        :class="['message', message.role]"
      >
        <div class="message-content">
          <div class="message-text" v-html="formatMessage(message.content)"></div>

          <!-- 工具使用标签 -->
          <div v-if="message.tool_used && message.tool_used !== 'none'" class="tool-badge">
            <span v-if="message.tool_used === 'knowledge'">📚 知识库</span>
            <span v-if="message.tool_used === 'search'">🔍 搜索</span>
          </div>

          <!-- TTS 按钮（预留） -->
          <button
            v-if="message.role === 'assistant'"
            class="tts-button"
            @click="speakMessage(message.content)"
            title="文本转语音"
          >
            🔊
          </button>
        </div>
      </div>

      <!-- 加载中指示器 -->
      <div v-if="isLoading" class="message assistant">
        <div class="message-content">
          <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="input-container">
      <!-- 文件上传按钮 -->
      <label class="upload-button" title="上传文件">
        📎
        <input
          type="file"
          ref="fileInput"
          @change="handleFileUpload"
          accept=".pdf,.txt,.md"
          style="display: none"
        />
      </label>

      <!-- 输入框 -->
      <input
        v-model="userInput"
        @keyup.enter="sendMessage"
        placeholder="输入消息..."
        :disabled="isLoading"
        class="message-input"
      />

      <!-- 发送按钮 -->
      <button
        @click="sendMessage"
        :disabled="isLoading || !userInput.trim()"
        class="send-button"
      >
        发送
      </button>
    </div>

    <!-- 上传进度提示 -->
    <div v-if="uploadProgress" class="upload-progress">
      {{ uploadProgress }}
    </div>
  </div>
</template>

<script>
export default {
  name: 'ChatInterface',
  data() {
    return {
      messages: [],
      userInput: '',
      isLoading: false,
      sessionId: this.generateSessionId(),
      uploadProgress: '',
      apiBaseUrl: 'http://localhost:8000'
    }
  },
  methods: {
    generateSessionId() {
      return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
    },

    async sendMessage() {
      if (!this.userInput.trim() || this.isLoading) return

      const userMessage = this.userInput.trim()
      this.userInput = ''

      // 添加用户消息
      this.messages.push({
        role: 'user',
        content: userMessage
      })

      this.isLoading = true
      this.scrollToBottom()

      try {
        // 使用流式输出
        await this.streamChat(userMessage)
      } catch (error) {
        console.error('发送消息失败:', error)
        this.messages.push({
          role: 'assistant',
          content: '抱歉，发生了错误：' + error.message
        })
      } finally {
        this.isLoading = false
        this.scrollToBottom()
      }
    },

    async streamChat(query) {
      const url = `${this.apiBaseUrl}/agent_chat_stream?query=${encodeURIComponent(query)}&session_id=${this.sessionId}`

      const eventSource = new EventSource(url)
      let assistantMessage = {
        role: 'assistant',
        content: '',
        tool_used: 'none'
      }
      this.messages.push(assistantMessage)

      return new Promise((resolve, reject) => {
        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)

            switch (data.type) {
              case 'metadata':
                assistantMessage.tool_used = data.tool_used
                break

              case 'content':
                assistantMessage.content += data.content
                this.scrollToBottom()
                break

              case 'status':
                // 显示状态消息（如"正在搜索..."）
                console.log('Status:', data.message)
                break

              case 'clear':
                // 清空之前的内容（用于搜索后重新生成）
                assistantMessage.content = ''
                break

              case 'done':
                eventSource.close()
                resolve()
                break

              case 'error':
                eventSource.close()
                reject(new Error(data.message))
                break
            }
          } catch (error) {
            console.error('解析消息失败:', error)
          }
        }

        eventSource.onerror = (error) => {
          console.error('SSE 错误:', error)
          eventSource.close()
          reject(error)
        }
      })
    },

    async handleFileUpload(event) {
      const file = event.target.files[0]
      if (!file) return

      this.uploadProgress = `正在上传 ${file.name}...`

      const formData = new FormData()
      formData.append('file', file)

      try {
        const response = await fetch(`${this.apiBaseUrl}/knowledge/upload_file`, {
          method: 'POST',
          body: formData
        })

        const result = await response.json()

        if (result.error) {
          this.uploadProgress = `上传失败: ${result.error}`
        } else {
          this.uploadProgress = `✅ ${result.message} (${result.chunks_added} 个片段)`

          // 3秒后清除提示
          setTimeout(() => {
            this.uploadProgress = ''
          }, 3000)
        }
      } catch (error) {
        console.error('上传失败:', error)
        this.uploadProgress = `上传失败: ${error.message}`
      }

      // 清空文件输入
      event.target.value = ''
    },

    speakMessage(text) {
      // TTS 功能预留
      // 这里可以集成 Edge TTS 或其他 TTS 服务
      console.log('TTS 功能待实现:', text)

      // 临时使用浏览器内置 TTS
      if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(text)
        utterance.lang = 'zh-CN'
        window.speechSynthesis.speak(utterance)
      } else {
        alert('您的浏览器不支持语音合成')
      }
    },

    formatMessage(content) {
      // 简单的 Markdown 格式化
      return content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>')
    },

    scrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.messagesContainer
        if (container) {
          container.scrollTop = container.scrollHeight
        }
      })
    }
  },

  mounted() {
    this.scrollToBottom()
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 800px;
  margin: 0 auto;
  background: #f5f5f5;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: white;
}

.message {
  margin-bottom: 16px;
  display: flex;
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.message-content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  position: relative;
}

.message.user .message-content {
  background: #007bff;
  color: white;
}

.message.assistant .message-content {
  background: #e9ecef;
  color: #333;
}

.message-text {
  word-wrap: break-word;
}

.tool-badge {
  margin-top: 8px;
  font-size: 12px;
  opacity: 0.7;
}

.tts-button {
  position: absolute;
  bottom: -8px;
  right: -8px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.tts-button:hover {
  background: #f0f0f0;
}

.typing-indicator {
  display: flex;
  gap: 4px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #999;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-10px);
  }
}

.input-container {
  display: flex;
  gap: 8px;
  padding: 16px;
  background: white;
  border-top: 1px solid #ddd;
}

.upload-button {
  font-size: 24px;
  cursor: pointer;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: white;
  transition: background 0.2s;
}

.upload-button:hover {
  background: #f0f0f0;
}

.message-input {
  flex: 1;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
}

.message-input:focus {
  outline: none;
  border-color: #007bff;
}

.send-button {
  padding: 12px 24px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.send-button:hover:not(:disabled) {
  background: #0056b3;
}

.send-button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.upload-progress {
  position: fixed;
  bottom: 80px;
  left: 50%;
  transform: translateX(-50%);
  background: #333;
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0,0,0,0.2);
  z-index: 1000;
}
</style>
