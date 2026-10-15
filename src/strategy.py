"""Evidence-based local visibility action plans."""
from src.leads import NICHES

CHECKS = {
    'Profile ownership verified': 'Have the owner verify and grant authorized profile access before editing.',
    'Correct primary category': 'Choose the most accurate available primary category; add relevant secondary categories.',
    'Accurate name, address and phone': 'Use the real business name and consistent address and public business number. Resolve duplicates.',
    'Hours and service area current': 'Update working and holiday hours; use a genuine service area and eligible business address.',
    'Services or products complete': 'Describe actual services and available products with useful detail and accurate prices where appropriate.',
    'Recent original photos': 'Publish current, original examples of the premises, work and products with owner permission.',
    'Genuine review process': 'Ask customers consistently for honest reviews and respond helpfully. Do not buy reviews or gate requests.',
    'Useful website linked': 'Build a useful website with service details, project proof, business contact information and enquiry tracking.',
    'Enquiry measurement in place': 'Record qualified calls, enquiry forms and booked consultations. Add campaign tags to the website link.',
}


def action_plan(niche, evidence):
    actions = []
    for label, recommendation in CHECKS.items():
        state = evidence.get(label, 'Unknown')
        if state != 'Verified complete':
            actions.append({'check': label, 'evidence': state, 'next_action': ('Verify with owner / profile evidence first. ' if state == 'Unknown' else '') + recommendation, 'phase': 'Days 1–14' if len(actions) < 4 else 'Days 15–45'})
    return actions


def niche_offer(niche):
    return NICHES[niche][1]
