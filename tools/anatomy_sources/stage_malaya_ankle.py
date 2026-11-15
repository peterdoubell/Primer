#!/usr/bin/env python3
"""Select genuinely available ankle/Achilles anatomy; never invent missing ligaments."""
from stage_malaya_knee import CACHE, main

SELECT = {
    'Bone_Tibia': ('Tibia', 'bone'),
    'Bone_Fibula': ('Fibula', 'bone'),
    'Bone_Talus': ('Talus', 'bone'),
    'Bone_Calcaneus': ('Calcaneus', 'bone'),
    'Bone_Navicular': ('Navicular', 'bone'),
    'Bone_Cuboid': ('Cuboid', 'bone'),
    'Bone_Medial Cuneiform': ('Medial cuneiform', 'bone'),
    'Bone_Intermediate Cuneiform': ('Intermediate cuneiform', 'bone'),
    'Bone_Lateral Cuneiform': ('Lateral cuneiform', 'bone'),
    'Tendon_Archilles': ('Achilles tendon', 'tendon'),
    'Muscle_Tibialis Anterior': ('Tibialis anterior source muscle unit', 'muscle'),
    'Muscle_Tibialis Posterior': ('Tibialis posterior source muscle unit', 'muscle'),
    'Muscle_Peroneus Longus': ('Fibularis longus source muscle unit', 'muscle'),
    'Muscle_Flexor Digitorum Longus': ('Flexor digitorum longus source muscle unit', 'muscle'),
    'Muscle_Flexor Hallucis Longus': ('Flexor hallucis longus source muscle unit', 'muscle'),
    'Muscle_Extensor Digitorum Longus': ('Extensor digitorum longus source muscle unit', 'muscle'),
    'Muscle_Extensor Hallucis Longus': ('Extensor hallucis longus source muscle unit', 'muscle'),
    'Muscle_Gastrocnemius Medial': ('Medial gastrocnemius', 'muscle'),
    'Muscle_Gastrocnemius Lateral': ('Lateral gastrocnemius', 'muscle'),
    'Muscle_Soleus': ('Soleus', 'muscle'),
}

if __name__ == '__main__':
    main(region='ankle', selection=SELECT, output=CACHE / 'malaya-ankle',
         focus_names={'Bone_Talus', 'Bone_Calcaneus'}, title='MRI-derived right ankle and Achilles')
