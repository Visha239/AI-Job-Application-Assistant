from app.services.resume_optimizer import ResumeOptimizer

optimizer = ResumeOptimizer()

output = optimizer.optimize_resume("Data Analyst")

print(f"Optimized resume created: {output}")