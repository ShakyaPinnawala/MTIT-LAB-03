from models import Course, CourseCreate, CourseUpdate

class CourseMockDataService:
    def __init__(self):
        self.courses = [
            Course(id=1, name="Data Structures & Algorithms", code="DS201", credits=4),
            Course(id=2, name="Operating Systems", code="OS202", credits=3),
            Course(id=3, name="Computer Networks", code="CN203", credits=3),
            Course(id=4, name="Machine Learning Fundamentals", code="ML204", credits=4),
            Course(id=5, name="Software Architecture", code="SA205", credits=3),
        ]
        self.next_id = 6

    def get_all_courses(self):
        return self.courses

    def get_course_by_id(self, course_id: int):
        return next((c for c in self.courses if c.id == course_id), None)

    def add_course(self, course_data: CourseCreate):
        new_course = Course(id=self.next_id, **course_data.dict())
        self.courses.append(new_course)
        self.next_id += 1
        return new_course

    def update_course(self, course_id: int, course_data: CourseUpdate):
        course = self.get_course_by_id(course_id)
        if not course:
            return None

        update_data = course_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(course, key, value)
        return course

    def delete_course(self, course_id: int):
        course = self.get_course_by_id(course_id)
        if course:
            self.courses.remove(course)
            return True
        return False