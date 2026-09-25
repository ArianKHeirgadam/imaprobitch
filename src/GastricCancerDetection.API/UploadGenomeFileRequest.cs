namespace GastricCancerDetection.API
{
    public class UploadGenomeFileRequest
    {
        public int SampleId { get; set; }
        public IFormFile File { get; set; } = null!;
        public int? UploadedByUserId { get; set; }
    }
}
