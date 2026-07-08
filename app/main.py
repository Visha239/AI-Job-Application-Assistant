import os

def show_menu():
    print("\n===================================")
    print("   AI JOB APPLICATION ASSISTANT")
    print("===================================")
    print("1. Read My Profile")
    print("2. Match Job Description")
    print("3. Generate Recruiter Email")
    print("4. Track Application")
    print("5. ATS Resume Tailor")
    print("6. Exit")


while True:
    show_menu()

    choice = input("\nChoose an option: ")

    if choice == "1":
        os.system("python app/profile_reader.py")

    elif choice == "2":
        os.system("python app/smart_matcher.py")

    elif choice == "3":
        os.system("python app/email_generator.py")

    elif choice == "4":
        os.system("python app/tracker.py")

    elif choice == "5":
        os.system("python app/resume_tailor.py")

    elif choice == "6":
        print("\nThank you for using AI Job Application Assistant.")
        break

    else:
        print("\nInvalid Choice! Please select between 1-6.")