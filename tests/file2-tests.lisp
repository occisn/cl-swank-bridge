(in-package cl-project-tests)

(parachute:define-test test-double
  (parachute:is = 0 (double 0))
  (parachute:is = 8 (double 4))
  (parachute:is = -6 (double -3)))

(parachute:define-test test-triple
  (parachute:is = 0 (triple 0))
  (parachute:is = 12 (triple 4))
  (parachute:is = -9 (triple -3)))
