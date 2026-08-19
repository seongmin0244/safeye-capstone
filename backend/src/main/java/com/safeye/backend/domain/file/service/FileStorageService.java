package com.safeye.backend.domain.file.service;

import org.springframework.web.multipart.MultipartFile;

public interface FileStorageService {

  String storeFile(MultipartFile file);
}
