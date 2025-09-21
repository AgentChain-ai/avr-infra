"""
CSV Processing Service with AI-powered field mapping
Handles bulk upload of student data from CSV/Excel files
"""
import pandas as pd
import json
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
import io
from datetime import datetime

from ..models.student import create_student
from ..models.field_config import get_active_fields
from ..config import settings

class CSVProcessor:
    """AI-powered CSV processing for student data upload"""
    
    def __init__(self, db: Session):
        self.db = db
        self.field_configs = get_active_fields(db)
    
    async def process_file_with_ai(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process uploaded file with AI-powered field mapping"""
        
        try:
            # Read the file into pandas DataFrame
            df = self._read_file(file_content, filename)
            
            if df.empty:
                return {
                    "success": False,
                    "message": "File is empty or could not be read",
                    "processed_count": 0,
                    "error_count": 0,
                    "warnings": [],
                    "field_mapping": {},
                    "sample_data": []
                }
            
            # Use AI to analyze headers and suggest mapping
            field_mapping = await self._ai_field_mapping(df.columns.tolist())
            
            # Process the data with mapped fields
            result = await self._process_dataframe(df, field_mapping)
            
            return {
                **result,
                "field_mapping": field_mapping
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error processing file: {str(e)}",
                "processed_count": 0,
                "error_count": 1,
                "warnings": [],
                "field_mapping": {},
                "sample_data": []
            }
    
    async def process_file_manual(self, file_content: bytes, filename: str, field_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Process uploaded file with manual field mapping"""
        
        try:
            # Read the file into pandas DataFrame
            df = self._read_file(file_content, filename)
            
            # Process with provided mapping
            result = await self._process_dataframe(df, field_mapping)
            
            return {
                **result,
                "field_mapping": field_mapping
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error processing file: {str(e)}",
                "processed_count": 0,
                "error_count": 1,
                "warnings": [],
                "field_mapping": field_mapping,
                "sample_data": []
            }
    
    def _read_file(self, file_content: bytes, filename: str) -> pd.DataFrame:
        """Read file content into pandas DataFrame"""
        
        try:
            if filename.lower().endswith('.csv'):
                # Try different encodings for CSV
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        df = pd.read_csv(io.BytesIO(file_content), encoding=encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise ValueError("Could not decode CSV file with any supported encoding")
            
            elif filename.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(io.BytesIO(file_content))
            
            else:
                raise ValueError(f"Unsupported file type: {filename}")
            
            # Clean column names
            df.columns = df.columns.str.strip().str.replace(' ', '_').str.lower()
            
            return df
            
        except Exception as e:
            raise ValueError(f"Error reading file: {str(e)}")
    
    async def _ai_field_mapping(self, column_headers: List[str]) -> Dict[str, str]:
        """Use AI to map CSV columns to database fields"""
        
        # Get available field configurations
        available_fields = {fc.field_name: fc.field_label for fc in self.field_configs}
        
        try:
            # Use OpenAI for intelligent field mapping
            import openai
            openai.api_key = settings.openai_api_key
            
            prompt = f"""
            I have a CSV file with these column headers: {column_headers}
            
            I need to map them to these available database fields:
            {json.dumps(available_fields, indent=2)}
            
            Also, these are common field patterns:
            - phone_number, phone, mobile, contact_number -> phone_number
            - student_name, name, full_name, student -> student_name
            - parent_name, father_name, mother_name, guardian -> parent_name
            - scholarship_amount, amount, scholarship -> scholarship_amount
            - scholarship_percentage, percentage, percent -> scholarship_percentage
            - test_score, score, marks -> test_score
            - rank_achieved, rank, position -> rank_achieved
            
            Return ONLY a JSON object mapping CSV columns to database fields.
            If a column doesn't match any field, map it to a similar field name.
            
            Example: {{"student_name": "student_name", "phone": "phone_number"}}
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            # Parse AI response
            ai_mapping = json.loads(response.choices[0].message.content.strip())
            
            # Validate and clean mapping
            validated_mapping = {}
            for csv_col, db_field in ai_mapping.items():
                if csv_col in column_headers:
                    validated_mapping[csv_col] = db_field
            
            return validated_mapping
            
        except Exception as e:
            print(f"AI mapping failed, using fallback: {e}")
            # Fallback to simple pattern matching
            return self._simple_field_mapping(column_headers)
    
    def _simple_field_mapping(self, column_headers: List[str]) -> Dict[str, str]:
        """Simple pattern-based field mapping fallback"""
        
        mapping_patterns = {
            'phone_number': ['phone', 'mobile', 'contact', 'number'],
            'student_name': ['name', 'student', 'full_name'],
            'parent_name': ['parent', 'father', 'mother', 'guardian'],
            'scholarship_amount': ['amount', 'scholarship', 'money'],
            'scholarship_percentage': ['percentage', 'percent', '%'],
            'test_score': ['score', 'marks', 'test'],
            'rank_achieved': ['rank', 'position', 'standing']
        }
        
        field_mapping = {}
        
        for col in column_headers:
            col_lower = col.lower()
            matched = False
            
            for db_field, patterns in mapping_patterns.items():
                if any(pattern in col_lower for pattern in patterns):
                    field_mapping[col] = db_field
                    matched = True
                    break
            
            if not matched:
                # Use the column name as-is for unmapped fields
                field_mapping[col] = col.lower().replace(' ', '_')
        
        return field_mapping
    
    async def _process_dataframe(self, df: pd.DataFrame, field_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Process DataFrame with field mapping and create student records"""
        
        processed_count = 0
        error_count = 0
        warnings = []
        sample_data = []
        
        # Validate required fields
        required_fields = [fc.field_name for fc in self.field_configs if fc.is_required]
        mapped_fields = set(field_mapping.values())
        
        missing_required = [field for field in required_fields if field not in mapped_fields]
        if missing_required:
            warnings.append(f"Missing required fields: {', '.join(missing_required)}")
        
        # Process each row
        for index, row in df.iterrows():
            try:
                # Extract phone number (required)
                phone_col = None
                for csv_col, db_field in field_mapping.items():
                    if db_field == 'phone_number':
                        phone_col = csv_col
                        break
                
                if not phone_col or pd.isna(row[phone_col]):
                    error_count += 1
                    warnings.append(f"Row {index + 1}: Missing phone number")
                    continue
                
                phone_number = str(row[phone_col]).strip()
                
                # Build student_data JSON
                student_data = {}
                for csv_col, db_field in field_mapping.items():
                    if csv_col in row and not pd.isna(row[csv_col]):
                        value = row[csv_col]
                        
                        # Type conversion based on field configuration
                        field_config = next((fc for fc in self.field_configs if fc.field_name == db_field), None)
                        if field_config:
                            if field_config.field_type == 'number':
                                try:
                                    value = int(float(value))
                                except ValueError:
                                    value = str(value)
                            elif field_config.field_type == 'currency':
                                try:
                                    value = float(value)
                                except ValueError:
                                    value = str(value)
                        
                        student_data[db_field] = value
                
                # Create student record
                new_student = create_student(
                    db=self.db,
                    phone_number=phone_number,
                    student_data=student_data,
                    priority=0
                )
                
                processed_count += 1
                
                # Add to sample data (first 10 records)
                if len(sample_data) < 10:
                    sample_data.append({
                        "row_number": index + 1,
                        "phone_number": phone_number,
                        "student_data": student_data
                    })
                
            except Exception as e:
                error_count += 1
                warnings.append(f"Row {index + 1}: {str(e)}")
        
        success = processed_count > 0
        message = f"Processed {processed_count} students successfully"
        if error_count > 0:
            message += f", {error_count} errors occurred"
        
        return {
            "success": success,
            "message": message,
            "processed_count": processed_count,
            "error_count": error_count,
            "warnings": warnings,
            "sample_data": sample_data
        }
