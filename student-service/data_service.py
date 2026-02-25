from models import Student, StudentCreate, StudentUpdate

class StudentMockDataService:
    def __init__(self):
        self.students = [
            Student(id=1, name="Nipuna Dassanayake", age=23, email="nipuna.d@example.com", course="Information Technology"),
            Student(id=2, name="Kasun Perera", age=21, email="kasun.p@example.com", course="Computer Science"),
            Student(id=3, name="Shehani Fernando", age=22, email="shehani.f@example.com", course="Software Engineering"),
            Student(id=4, name="Dilshan Jayawardana", age=24, email="dilshan.j@example.com", course="Data Science"),
            Student(id=5, name="Amaya Silva", age=20, email="amaya.s@example.com", course="Cyber Security"),
        ]
        self.next_id = 6

    def get_all_students(self):
        return self.students

    def get_student_by_id(self, student_id: int):
        return next((s for s in self.students if s.id == student_id), None)

    def add_student(self, student_data: StudentCreate):
        new_student = Student(id=self.next_id, **student_data.dict())
        self.students.append(new_student)
        self.next_id += 1
        return new_student

    def update_student(self, student_id: int, student_data: StudentUpdate):
        student = self.get_student_by_id(student_id)
        if not student:
            return None

        update_data = student_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(student, key, value)
        return student

    def delete_student(self, student_id: int):
        student = self.get_student_by_id(student_id)
        if student:
            self.students.remove(student)
            return True
        return False