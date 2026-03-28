(in-package cl-project-tests)

(parachute:define-test test-factorial
  (parachute:is = 1 (factorial 0))
  (parachute:is = 1 (factorial 1))
  (parachute:is = 120 (factorial 5))
  (parachute:is = 3628800 (factorial 10)))

(parachute:define-test test-collatz-steps
  (parachute:is = 0 (collatz-steps 1))
  (parachute:is = 1 (collatz-steps 2))
  (parachute:is = 111 (collatz-steps 27)))
