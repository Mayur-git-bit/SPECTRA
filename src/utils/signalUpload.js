import * as api from '../api';

export async function uploadAndAnalyzeSignal(selectedFile, onStatus) {
  const uploadResult = await api.uploadFile(selectedFile);
  const jobId = uploadResult.job_id;

  await api.analyzeSignal(jobId);

  const analysis = await api.pollAnalysis(jobId, (status) => {
    onStatus?.(status);
  });

  const [waveform, spectrum, waterfall, constellation, bitstream] = await Promise.all([
    api.getWaveform(jobId),
    api.getSpectrum(jobId),
    api.getWaterfall(jobId),
    api.getConstellation(jobId).catch(() => null),
    api.getBitstream(jobId).catch(() => null),
  ]);

  return {
    jobId,
    status: analysis,
    analysis,
    waveform,
    spectrum,
    waterfall,
    constellation,
    bitstream,
    file: uploadResult.filename
      ? {
          name: uploadResult.filename,
          size_bytes: uploadResult.size_bytes,
        }
      : null,
  };
}