# Turn clean marks into letter grades for the exams office.
marks <- read.csv("clean_marks.csv", stringsAsFactors = FALSE)
grade <- function(m) {
  if (m >= 70) "A" else if (m >= 60) "B" else if (m >= 50) "C" else if (m >= 40) "D" else "U"
}
marks$grade <- sapply(marks$mark, grade)
write.csv(marks[, c("student_id", "mark", "grade")], "grades_final.csv", row.names = FALSE)
