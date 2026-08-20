package com.safeye.backend.domain.dangerevent.repository;

import com.safeye.backend.domain.dangerevent.entity.DangerEvent;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface DangerEventRepository extends JpaRepository<DangerEvent, UUID> {

}
