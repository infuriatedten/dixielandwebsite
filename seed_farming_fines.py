from app import create_app, db
from app.models import Fine

# Create an application context
app = create_app()
app.app_context().push()

def seed_farming_fines():
    """
    Seeds the database with farming-related fines.
    It checks if a fine with the same name already exists before adding it.
    """
    farming_fines = [
        {
            "name": "Improper Waste Disposal",
            "description": "Leaving farm waste, such as empty fertilizer bags, oil containers, or old equipment, in a non-designated area.",
            "amount": 250
        },
        {
            "name": "Unsafe Vehicle Operation",
            "description": "Operating a farm vehicle (tractor, harvester, etc.) on public roads without proper lighting or safety signals.",
            "amount": 150
        },
        {
            "name": "Livestock at Large",
            "description": "Allowing farm animals to roam freely outside of their designated, fenced-in area, posing a risk to public safety and property.",
            "amount": 200
        },
        {
            "name": "Unregulated Water Diversion",
            "description": "Illegally diverting water from a public river or lake for irrigation without a permit.",
            "amount": 500
        },
        {
            "name": "Off-label Pesticide Use",
            "description": "Using a chemical pesticide or herbicide in a manner not specified by its official instructions, risking environmental damage.",
            "amount": 400
        },
        {
            "name": "Failure to Control Noxious Weeds",
            "description": "Allowing designated noxious weeds (e.g., thistle, bindweed) to grow uncontrolled and spread to neighboring properties.",
            "amount": 300
        },
        {
            "name": "Unlicensed Sale of Produce",
            "description": "Selling produce directly to the public or to businesses without the required food safety and sales permits.",
            "amount": 350
        },
        {
            "name": "Soil Erosion Negligence",
            "description": "Failing to implement basic soil erosion control measures (e.g., contour plowing, cover crops) on steeply sloped fields, leading to runoff.",
            "amount": 450
        }
    ]

    try:
        fines_added_count = 0
        for fine_data in farming_fines:
            # Check if a fine with the same name already exists
            existing_fine = Fine.query.filter_by(name=fine_data["name"]).first()
            if not existing_fine:
                new_fine = Fine(**fine_data)
                db.session.add(new_fine)
                fines_added_count += 1
                print(f"Adding fine: '{fine_data['name']}'")
            else:
                print(f"Skipping fine: '{fine_data['name']}' already exists.")

        if fines_added_count > 0:
            db.session.commit()
            print(f"\nSuccessfully added {fines_added_count} new farming fines.")
        else:
            print("\nNo new farming fines to add.")

    except Exception as e:
        db.session.rollback()
        print(f"An error occurred while seeding farming fines: {e}")

if __name__ == '__main__':
    print("Running farming fines seeder...")
    seed_farming_fines()
    print("Seeding complete.")
