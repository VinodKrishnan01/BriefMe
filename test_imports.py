# Test if routes import correctly

print("🔍 Testing route imports...")

try:
    from routes.briefs import api as briefs_ns
    print(f"✅ briefs_ns imported: {briefs_ns}")
    print(f"✅ Type: {type(briefs_ns)}")
    
    # Check if it has resources
    if hasattr(briefs_ns, 'resources'):
        print(f"✅ Resources: {briefs_ns.resources}")
    else:
        print("❌ No resources found in namespace")
        
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()

print("\n🔍 Testing service imports...")

try:
    from services.firestore_service_mock import FirestoreService
    print(f"✅ FirestoreService imported")
except Exception as e:
    print(f"❌ FirestoreService import failed: {e}")

try:
    from services.gemini_service_mock import GeminiService
    print(f"✅ GeminiService imported")
except Exception as e:
    print(f"❌ GeminiService import failed: {e}")