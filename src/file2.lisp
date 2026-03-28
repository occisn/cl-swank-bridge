(in-package cl-project)

(defun double (x)
  "Return twice the value of X."
  (declare (type fixnum x))
  (* 2 x))

(defun triple (x)
  "Return three times the value of X."
  (declare (type fixnum x))
  (* 3 x))

(defun main ()
  "Entry point displaying demo output."
  (format t "factorial(10) = ~A~%" (factorial 10))
  (format t "collatz-steps(27) = ~A~%" (collatz-steps 27))
  (format t "double(21) = ~A~%" (double 21))
  (format t "triple(14) = ~A~%" (triple 14)))
