from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, computed_field
from typing import Annotated, Literal,Optional
import json

app = FastAPI()
 
class Patient(BaseModel):
    id: Annotated[str, Field(...,description="The ID of the patient", example="POO1")]
    name: Annotated[str, Field(..., description="The name of the patient", example="John Doe")]
    city: Annotated[str, Field(..., description="The city of the patient", example="New York")]
    age:Annotated[int, Field(..., gt=0, lt=120, description="The age of the patient", example=30)]    
    gender: Annotated[Literal['male', 'female', 'other'], Field(..., description='Gender of the patient')]
    height: Annotated[float, Field(..., gt=0, description="The height of the patient in cm", example=175.5)]
    weight: Annotated[float, Field(..., gt=0, description="The weight of the patient in kg", example=70.2)]
    
    @computed_field
    @property
    def bmi(self) -> float:
        """Calculate the Body Mass Index (BMI) of the patient."""
        return round(self.weight / ((self.height / 100) ** 2), 2)


    @computed_field
    @property
    def verdict(self) -> str:
        """Determine the BMI verdict based on the BMI value."""
        if self.bmi < 18.5:
            return "Underweight"
        elif 18.5 <= self.bmi < 24.9:
            return "Normal weight"
        elif 25 <= self.bmi < 29.9:
            return "Overweight"
        else:
            return "Obesity"
    

class PatientUpdate(BaseModel):
    name: Annotated[Optional[str], Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    age:Annotated[Optional[int], Field(default=None, gt=0)]    
    gender: Annotated[Optional[Literal['male', 'female', 'other']], Field(default=None)]
    height: Annotated[Optional[float], Field( default=None,gt=0)]
    weight: Annotated[Optional[float], Field(default=None, gt=0)]
    

    
def load_data():
    with open('patients.json', 'r') as file: # read
        data= json.load(file)
    return data

def save_data(data):
    with open('patients.json', 'w') as file: # write
        json.dump(data, file)
    


#route
@app.get("/") # fetch data from sever and see we use get method
def read_root():
    return {"message": "Patient Management System"}

@app.get("/about")
def about():
    return {"message": "API to manage patient data"}

@app.get("/view")
def view():
    data = load_data()
    return data

@app.get("/view/{patient_id}")
def view_patient(patient_id: str= Path(..., description="The ID of the patient to DB", example="POO1")):
    data = load_data()
    if patient_id in data:
        return data[patient_id]
    #return {"error": "Patient not found"} 
    #using custom exception
    raise HTTPException(status_code=404, detail="Patient not found")

@app.get("/sort")
def sort_patients(sort_by: str = Query(..., description="sort by height, weight or bmi"), order: str=Query('asc', description= "sort in asc or desc order" )):
    valid_fields = ['height', 'weight', 'bmi']
    if sort_by not in valid_fields:
        raise HTTPException(status_code=400, detail=f"Invalid field select from {valid_fields}")
                            
    if order not in ['asc', 'desc']:
        raise HTTPException(status_code=400, detail="Order must be 'asc' or 'desc'")
    data = load_data()
    
    sort_order = True if order == 'desc' else False
    
    sorted_data = sorted(data.values(), key=lambda x: x[sort_by], reverse=sort_order)
    return sorted_data

@app.post("/create")
def create_patient(patient: Patient):
    #load existing data
    data = load_data()
    # Check if patient ID already exists
    if patient.id in data:
        raise HTTPException(status_code=400, detail="Patient ID already exists")
    
    #converting pydantic model to dict and add to data
    data[patient.id]=patient.model_dump(exclude=["id"])
    
    #save into json file
    save_data(data)
    
    return JSONResponse(status_code=201, content={"message": "Patient created successfully", "patient_id": patient.id})

@app.put("/update/{patient_id}")
def update_patient(patient_id: str, patient_update: PatientUpdate):
    
    data = load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    existing_patient_info = data[patient_id]
    
    update_patient_info = patient_update.model_dump(exclude_unset=True)
    
    for key, value in update_patient_info.items():
        existing_patient_info[key] = value
        
    #existing_patient_info-> make new pydantic object of Patient that mean it will
    #compute again with the new values -> converted pydaniic object to dict
    existing_patient_info['id'] = patient_id  # Ensure the ID remains unchanged 
    patient_pydantic_object = Patient(**existing_patient_info)
    # pydantic object to dict
    existing_patient_info = patient_pydantic_object.model_dump(exclude=["id"])
    
    data[patient_id] = existing_patient_info
    
    save_data(data)
    
    return JSONResponse(status_code=200, content={"message": "Patient updated successfully", "patient_id": patient_id})
    
@app.delete("/delete/{patient_id}")
def delete_patient(patient_id: str):
    data = load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")
    # Remove the patient from the data
    del data[patient_id]
    
    save_data(data)
    
    return JSONResponse(status_code=200, content={"message": "Patient deleted successfully", "patient_id": patient_id})

