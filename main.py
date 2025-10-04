# this is my code for my new to-do list software
task = []

if __name__ == "__main__":
    ## we are going to create a loop
    print("\nWelcome to your To-Do List!")
while True:
    print("\n Make your choice! \n--------------------" )
    print("1. Add a task")
    print("2. View tasks")
    print("3. Remove a task")
    print("4. Exit")

    choice = input("Enter your choice: ")

    if choice == '1':
        new_task = input("Enter the task: ")
        task.append(new_task)
        print(f'Task "{new_task}" added.')
    elif choice == '2':
        print("Tasks:")
        for i, t in enumerate(task, 0):
            print(f"{i}. {t}")
    elif choice == '3':
        for i, t in enumerate(task, 0):
            print(f"{i}. {t}")
        task_to_remove = int(input("Enter the task to remove: "))
        if task_to_remove >= 0 and task_to_remove < len(task):
            task.pop(task_to_remove)
            print(f'Task "#{task_to_remove}" removed.')
        else:
            print(f'Task "{task_to_remove}" not found.')
    elif choice == '4':
        print("Goodbye!")
        break
    else:
        print("Invalid choice. Please try again.")
