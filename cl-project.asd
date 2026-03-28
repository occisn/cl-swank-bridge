(asdf:defsystem "cl-project"
  :name "cl-project"
  :version "0.1.0"
  :author "John Doe"
  :licence "MIT"
  :description "Minimal demo project for the cl-swank-bridge"
  :depends-on (:parachute)
  :serial t
  :around-compile (lambda (next)
                    (proclaim '(optimize (debug 3)
                                (safety 3)
                                (speed 0)))
                    (funcall next))
  :components ((:file "package")
               (:module "src"
                :components
                ((:file "file1")
                 (:file "file2"))))
  :in-order-to ((asdf:test-op (asdf:test-op :cl-project-tests))))
