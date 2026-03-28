(in-package cl-project)

(defun factorial (n)
  "Return N! for non-negative integer N."
  (declare (type (integer 0) n))
  (if (zerop n)
      1
      (* n (factorial (1- n)))))

(defun collatz-steps (n)
  "Return the number of Collatz steps to reach 1 from positive integer N."
  (declare (type (integer 1) n))
  (loop for x = n then (if (evenp x) (/ x 2) (1+ (* 3 x)))
        for steps from 0
        until (= x 1)
        finally (return steps)))
