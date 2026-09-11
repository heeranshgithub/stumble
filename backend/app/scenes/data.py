"""The six scenes. Code, not data: they change with a commit, not a migration."""

from pydantic import BaseModel

from app.models.scene import SceneDto, SceneStatus


class Scene(BaseModel):
    id: str
    title: str
    color: str
    goal: str
    goal_fr: str
    character_name: str
    character_role: str
    opening_line: str
    opening_line_en: str
    vocab: list[str]
    order: int


SCENES: list[Scene] = [
    Scene(
        id="cafe",
        title="Café",
        color="cafe",
        goal="Order a coffee and pay.",
        goal_fr="Commander un café et payer.",
        character_name="Léa",
        character_role="barista",
        opening_line="Bonjour ! Qu'est-ce que je vous sers ?",
        opening_line_en="Hello! What can I get you?",
        vocab=["café", "au lait", "combien", "s'il vous plaît", "l'addition"],
        order=1,
    ),
    Scene(
        id="pharmacie",
        title="Pharmacie",
        color="pharmacie",
        goal="Get something for a headache.",
        goal_fr="Obtenir quelque chose contre le mal de tête.",
        character_name="Karim",
        character_role="pharmacist",
        opening_line="Bonjour, je peux vous aider ?",
        opening_line_en="Hello, can I help you?",
        vocab=["mal à la tête", "ordonnance", "sirop", "comprimé", "combien de fois"],
        order=2,
    ),
    Scene(
        id="apartment",
        title="Apartment viewing",
        color="apartment",
        goal="Get the rent and the move-in date.",
        goal_fr="Obtenir le montant du loyer et la date d'entrée.",
        character_name="Mme Roux",
        character_role="landlady",
        opening_line="Entrez, entrez. Alors, voilà le salon. Vous cherchez depuis longtemps ?",
        opening_line_en=(
            "Come in, come in. So, this is the living room. Have you been looking for long?"
        ),
        vocab=["loyer", "appart", "mois", "charges", "je peux"],
        order=3,
    ),
    Scene(
        id="bill",
        title="Disputing a phone bill",
        color="bill",
        goal="Get one charge removed from the bill.",
        goal_fr="Faire retirer un frais de la facture.",
        character_name="Agent",
        character_role="customer service agent",
        opening_line="Service client, bonjour. C'est à quel sujet ?",
        opening_line_en="Customer service, hello. What is it about?",
        vocab=["facture", "prélèvement", "rembourser", "je ne comprends pas"],
        order=4,
    ),
    Scene(
        id="doctor",
        title="Doctor",
        color="doctor",
        goal="Describe a symptom and get advice.",
        goal_fr="Décrire un symptôme et obtenir un conseil.",
        character_name="Dr Lemaire",
        character_role="doctor",
        opening_line="Bonjour, asseyez-vous. Qu'est-ce qui vous amène ?",
        opening_line_en="Hello, have a seat. What brings you in?",
        vocab=["depuis", "douleur", "fièvre", "ça fait mal"],
        order=5,
    ),
    Scene(
        id="interview",
        title="Job interview",
        color="interview",
        goal="Answer three interview questions.",
        goal_fr="Répondre à trois questions d'entretien.",
        character_name="Sophie",
        character_role="recruiter",
        opening_line="Merci d'être venu. Pour commencer, parlez-moi un peu de vous.",
        opening_line_en="Thanks for coming. To start, tell me a little about yourself.",
        vocab=["expérience", "j'ai travaillé", "pourquoi", "disponible"],
        order=6,
    ),
]

_BY_ID = {scene.id: scene for scene in SCENES}


def get_scene(scene_id: str) -> Scene | None:
    return _BY_ID.get(scene_id)


def to_dto(scene: Scene, status: SceneStatus, uses_due_cards: list[str] | None = None) -> SceneDto:
    return SceneDto(
        id=scene.id,
        title=scene.title,
        color=scene.color,
        goal=scene.goal,
        character_name=scene.character_name,
        character_role=scene.character_role,
        order=scene.order,
        status=status,
        uses_due_cards=uses_due_cards or [],
    )
