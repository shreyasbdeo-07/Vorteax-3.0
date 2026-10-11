
from sentence_transformers import SentenceTransformer

print("Loading RozgarLink pretrained model...")

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

skills = [
    "Building web applications using React",
    "Developing user interfaces with React.js",
    "Repairing automobile engines",
]

embeddings = model.encode(
    skills,
    normalize_embeddings=True
)

similarities = model.similarity(embeddings, embeddings)

print("\nSkill similarity results:")

for i in range(len(skills)):
    for j in range(i + 1, len(skills)):
        score = similarities[i][j].item()
        print(f"\nSkill 1: {skills[i]}")
        print(f"Skill 2: {skills[j]}")
        print(f"Similarity score: {score:.3f}")

print("\nModel loaded and tested successfully!")
