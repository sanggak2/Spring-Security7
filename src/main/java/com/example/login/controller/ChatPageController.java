package com.example.login.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.stereotype.Controller; // 👈 RestController 아님!
import org.springframework.web.bind.annotation.GetMapping;

@Tag(name = "Chat View Controller", description = "챗봇 컨트롤러입니다")
@Controller // 👈 "난 화면(HTML)을 보여줄 거야!"
public class ChatPageController {

    @Operation(summary = "챗봇", description = "챗봇입니다")
    @GetMapping("/chat") // 주소창에 localhost:8080/chat 입력 시
    public String chatPage() {
        return "chat"; // templates/chat.mustache 파일을 찾아감
    }
}