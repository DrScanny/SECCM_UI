
def test():
    x=5

    return x



class McGill():
    number=0

    def __init__(self, name='Unidentified', age:int=0):
        self.name= name
        self.age= age
        McGill.number= McGill.number+1

    def printNameAge(self):
        print(self.name, self.age)

    def printStuff(self):
        print('class method inheritance')

class Student(McGill):

    def __init__(self, status='undergraduate'):
        #super().__init__()
        self.status= status



person1= McGill('Danny', 42)
person2= McGill('Theo')

student1= Student(status= 'Research Associate')
student1.printStuff()
