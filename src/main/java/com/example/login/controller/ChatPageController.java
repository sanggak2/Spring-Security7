package com.example.login.controller;

import org.springframework.stereotype.Controller; // 👈 RestController 아님!
import org.springframework.web.bind.annotation.GetMapping;

@Controller // 👈 "난 화면(HTML)을 보여줄 거야!"
public class ChatPageController {

    @GetMapping("/chat") // 주소창에 localhost:8080/chat 입력 시
    public String chatPage() {
        return "chat"; // templates/chat.mustache 파일을 찾아감
    }
}