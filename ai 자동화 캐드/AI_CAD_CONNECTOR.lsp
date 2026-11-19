;;; =========================================================
;;; AI CAD 자연어 자동 작도 커넥터 (AutoCAD 2023 전용)
;;; 지원 공종: 금속 하지틀(각파이프), 화스너 브라켓, 외장 판넬(알루미늄/복합판넬)
;;; 명령어: AI 또는 AICAD
;;; =========================================================

(defun c:AI ()
  (c:AICAD)
)

(defun c:AICAD (/ user_input prompt_file scr_file py_cmd file cur_dir t0 timeout_ms)
  (vl-load-com)
  ;; 작업 디렉토리 설정
  (setq cur_dir "d:\\AI 1인 기업 test\\ai 자동화 캐드")
  (setq prompt_file (strcat cur_dir "\\prompt_input.txt"))
  (setq scr_file (strcat cur_dir "\\ai_draw_output.scr"))
  
  ;; 1. 사용자로부터 자연어 도면 사양 입력 받기
  (setq user_input (getstring T "\n[AI 도면 자동화 - AutoCAD 2023] 사양을 자연어로 입력하세요: "))
  
  (if (and user_input (/= user_input ""))
    (progn
      ;; 이전 스크립트 파일이 남아있으면 삭제하여 충돌 방지
      (if (findfile scr_file)
        (vl-file-delete scr_file)
      )

      ;; 2. 입력된 프롬프트를 텍스트 파일로 저장
      (setq file (open prompt_file "w"))
      (write-line user_input file)
      (close file)
      (princ "\n[AI] 자연어 해석 및 AutoCAD 2023 작도 스크립트 생성 중...")
      
      ;; 3. 파이썬 AI 작도 엔진 백그라운드 호출
      (setq py_cmd (strcat "python \"" cur_dir "\\ai_cad_engine.py\""))
      (startapp py_cmd)
      
      ;; 4. 생성 완료 대기 (AutoCAD 내장 DELAY 및 타임아웃 5초)
      (setq timeout_ms 5000)
      (setq t0 (getvar "MILLISECS"))
      (while (and (not (findfile scr_file))
                  (< (- (getvar "MILLISECS") t0) timeout_ms))
        (command "DELAY" 150)
      )
      
      ;; 추가 안전 딜레이 100ms
      (command "DELAY" 100)

      ;; 5. 생성된 작도 스크립트 실행
      (if (findfile scr_file)
        (progn
          (if (vl-symbol-value 'command-s)
            (command-s "SCRIPT" scr_file)
            (command "SCRIPT" scr_file)
          )
          (princ "\n[AI] ✅ 도면 작도가 성공적으로 완료되었습니다!")
        )
        (princ "\n[AI] ❌ 도면 생성 시간 초과 또는 파이썬 실행 오류입니다.")
      )
    )
    (princ "\n[AI] 작도 입력이 취소되었습니다.")
  )
  (princ)
)

(princ "\n=================================================================")
(princ "\n[AutoCAD 2023 - AI 금속 도면 자동화 커넥터 업데이트 완료]")
(princ "\n명령창에 'AI' 를 입력하여 자연어로 도면을 작성하세요.")
(princ "\n=================================================================\n")
(princ)
