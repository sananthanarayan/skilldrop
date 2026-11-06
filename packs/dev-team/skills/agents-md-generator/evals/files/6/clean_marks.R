# Fill blank marks with 0 and apply the 10% late penalty.
marks <- read.csv("raw_marks.csv", stringsAsFactors = FALSE)
marks$mark[is.na(marks$mark)] <- 0
marks$mark <- ifelse(marks$late == "Y", round(marks$mark * 0.9), marks$mark)
write.csv(marks, "clean_marks.csv", row.names = FALSE)
