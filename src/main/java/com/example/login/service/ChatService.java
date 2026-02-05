package com.example.login.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import java.util.HashMap;
import java.util.Map;

@Service
public class ChatService {

    @Value("${openai.chatbot.url}")
    private String pythonServerUrl;

    public String getChatResponse(String userMessage) {
        // 1. 요청 도구 생성
        RestTemplate restTemplate = new RestTemplate();

        // 2. 헤더 설정
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        // 3. 바디 설정
        Map<String, String> requestBody = new HashMap<>();
        requestBody.put("message", userMessage);

        // 4. 편지 봉투에 담기
        HttpEntity<Map<String, String>> entity = new HttpEntity<>(requestBody, headers);

        try {
            Map response = restTemplate.postForObject(pythonServerUrl, entity, Map.class);

            return response.get("reply").toString();

        } catch (Exception e) {
            e.printStackTrace();
            return "죄송합니다. AI 서버와 연결이 원활하지 않습니다.";
        }
    }
}