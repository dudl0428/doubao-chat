/**
 * 个人AI聊天 - 主JavaScript文件
 */

// 处理移动端导航栏折叠
document.addEventListener('DOMContentLoaded', function() {
    // 设置CSRF令牌保护
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    if (csrfToken) {
        // 为所有AJAX请求添加CSRF令牌
        document.addEventListener('fetch', function(event) {
            if (event.request.method !== 'GET') {
                const headers = new Headers(event.request.headers);
                headers.append('X-CSRFToken', csrfToken);
                event.request = new Request(
                    event.request.url,
                    {
                        method: event.request.method,
                        headers: headers,
                        body: event.request.body,
                        mode: event.request.mode,
                        credentials: event.request.credentials,
                        cache: event.request.cache,
                        redirect: event.request.redirect,
                        referrer: event.request.referrer,
                        integrity: event.request.integrity
                    }
                );
            }
        });
    }

    // 自动关闭警告消息
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const closeButton = alert.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        }, 5000);
    });

    // 处理Markdown渲染
    function renderMarkdown() {
        const assistantMessages = document.querySelectorAll('.assistant-message');
        assistantMessages.forEach(message => {
            // 处理代码块
            let content = message.innerHTML;
            
            // 如果内容中不包含HTML标签，则处理换行
            if (!content.includes('<p>') && !content.includes('<br>') && !content.includes('<div>')) {
                // 替换换行符为<br>标签
                content = content.replace(/\n/g, '<br>');
            }
            
            // 处理代码块
            if (content.includes('```')) {
                // 替换代码块
                content = content.replace(/```(\w*)([\s\S]*?)```/g, function(match, language, code) {
                    return `<pre class="code-block"><code class="${language}">${code.trim()}</code></pre>`;
                });
                
                // 替换内联代码
                content = content.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
            }
            
            // 处理列表
            content = content.replace(/^\s*[-*]\s+(.+)$/gm, '<li>$1</li>');
            content = content.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');
            
            // 处理标题
            content = content.replace(/^###\s+(.+)$/gm, '<h5>$1</h5>');
            content = content.replace(/^##\s+(.+)$/gm, '<h4>$1</h4>');
            content = content.replace(/^#\s+(.+)$/gm, '<h3>$1</h3>');
            
            // 处理粗体和斜体
            content = content.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
            content = content.replace(/\*([^*]+)\*/g, '<em>$1</em>');
            
            message.innerHTML = content;
        });
    }

    // 初始渲染Markdown
    renderMarkdown();

    // 处理表单提交时的按钮加载状态
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                
                // 如果按钮有图标，添加加载动画
                if (submitButton.querySelector('i')) {
                    const icon = submitButton.querySelector('i');
                    const originalClass = icon.className;
                    icon.className = 'fas fa-spinner fa-spin';
                    
                    // 表单提交完成后恢复按钮状态
                    setTimeout(() => {
                        submitButton.disabled = false;
                        icon.className = originalClass;
                    }, 2000);
                } else {
                    // 表单提交完成后恢复按钮状态
                    setTimeout(() => {
                        submitButton.disabled = false;
                    }, 2000);
                }
            }
        });
    });

    // 处理文本区域自动调整高度
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    });
}); 