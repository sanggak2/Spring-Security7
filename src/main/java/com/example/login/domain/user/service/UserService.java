package com.example.login.domain.user.service;

import com.example.login.domain.user.dto.UserDto;
import com.example.login.domain.user.entity.UserEntity;
import com.example.login.domain.user.entity.UserRole;
import com.example.login.domain.user.repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class UserService implements UserDetailsService {
    @Autowired
    private UserRepository userRepository;
    @Autowired
    private PasswordEncoder passwordEncoder;

    //회원가입
    public void join(UserDto userDto) {
        String username = userDto.getUsername();
        String password = userDto.getPassword();

        UserEntity userEntity = new UserEntity();
        userEntity.setUsername(username);
        userEntity.setPassword(passwordEncoder.encode(password));
        userEntity.setRole(UserRole.USER);

        userRepository.save(userEntity);
    }

    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        UserEntity entity = userRepository.findByUsername(username).orElse(null);
        if (entity == null) {
            throw new UsernameNotFoundException(username);
        }
        return User.builder().username(entity
                .getUsername())
                .password(entity.getPassword())
                .roles(entity.getRole().name())
                .build();

    }
}
